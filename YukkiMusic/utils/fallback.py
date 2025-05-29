#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import logging
from YukkiMusic.platforms import saavn

logger = logging.getLogger(__name__)

async def download(title, video):
    try:
        path, details = await saavn.download(title)
        return path, details, video
    except Exception as e:
        logger.error("Fallback download failed", exc_info=True)
        raise ValueError("Failed to download song from youtube") from e
