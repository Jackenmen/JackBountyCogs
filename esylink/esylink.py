import logging
from typing import Any, Dict, Literal, Mapping

import aiohttp
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import NoParseOptional as Optional
from redbot.core.utils.chat_formatting import inline

from . import errors
from .utils import json_or_text

log = logging.getLogger("red.jackbountycogs.esylink")

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class EsyLink(commands.Cog):
    """Shorten links with EsyL.ink."""

    def __init__(self, bot: Red) -> None:
        super().__init__()
        self.bot = bot
        self._session = aiohttp.ClientSession()
        self._token: str

    async def initialize(self) -> None:
        await self._set_token()

    def cog_unload(self) -> None:
        self._session.detach()

    __del__ = cog_unload

    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    async def _set_token(self, api_tokens: Optional[Mapping[str, str]] = None) -> None:
        if api_tokens is None:
            api_tokens = await self.bot.get_shared_api_tokens("esylink")
        self._token = api_tokens.get("api_key", "")

    async def shorten_url(self, url: str, custom_alias: Optional[str] = None) -> str:
        """
        Shorten link using EsyL.ink API.

        Raises
        ------
        errors.HTTPException
            Unexpected HTTP error happened.
        errors.UserError
            User error has been returned by API.
        """
        data = await self._request(url, custom_alias)
        if data["error"] == 1:
            raise errors.UserError(data["msg"])
        return data["short"]

    async def _request(
        self, url: str, custom_alias: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {
            "key": self._token,
            "url": url,
        }
        if custom_alias is not None:
            params["custom"] = custom_alias

        async with self._session.get(
            "https://esyl.ink/api/",
            params=params,
            # this API doesn't seem to like user agent header
            skip_auto_headers={aiohttp.hdrs.USER_AGENT},
        ) as resp:
            data = await json_or_text(resp)
            if 300 > resp.status >= 200:
                assert isinstance(data, dict), "mypy"
                return data

            raise errors.HTTPException(resp, data)

    @commands.command()
    async def sl(
        self, ctx: commands.Context, url: str, alias: Optional[str] = None
    ) -> None:
        """Shorten links with EsyL.ink."""
        async with ctx.typing():
            await self._sl_command(ctx, url, alias)

    async def _sl_command(
        self, ctx: commands.Context, url: str, alias: Optional[str] = None
    ) -> None:
        try:
            shortened_url = await self.shorten_url(url, alias)
        except errors.UserError as e:
            # this is expected error per API documentation, just send it to the user
            await ctx.send(str(e))
        except errors.HTTPException as e:
            # non-200 errors shouldn't generally happen,
            # but let's put some friendly messages just in case
            log.error(str(e))
            if e.status >= 500:
                await ctx.send(
                    "EsyL.ink API experiences some issues right now."
                    " Try again later."
                )
            else:
                await ctx.send(
                    "EsyL.ink API can't process this request."
                    " If this keeps happening, inform bot's owner about this error."
                )
        else:
            await ctx.send(f"Here's your shortened URL: <{shortened_url}>")

    @commands.is_owner()
    @commands.command()
    async def esyinfo(self, ctx: commands.Context) -> None:
        """Instructions to set the EsyL.ink API key."""
        command = inline(
            f"{ctx.clean_prefix}set api esylink api_key PUT_YOUR_API_KEY_HERE"
        )
        message = (
            "1. Sign up to https://esyl.ink/ for a free account.\n"
            "2. Click Tools & Integrations in the menu on the left.\n"
            "3. Select Developer API.\n"
            f"4. Copy your API key and run the command: {command}"
        )
        await ctx.maybe_send_embed(message)

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ) -> None:
        if service_name != "esylink":
            return

        await self._set_token(api_tokens)
