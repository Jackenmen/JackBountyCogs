from redbot.core.bot import Red

from .esylink import EsyLink

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot: Red) -> None:
    cog = EsyLink(bot)
    await cog.initialize()
    bot.add_cog(cog)
