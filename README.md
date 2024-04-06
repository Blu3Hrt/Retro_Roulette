
# Retro Roulette

## Overview
*Retro Roulette* is a gaming management and streaming tool that enhances the gaming experience with game shuffling, session management, and Twitch integration. This application is inspired by *BizHawk Shuffler 2* and is perfect for gamers and streamers who love variety and interaction.

## Installation
Download the latest release from the [Releases](https://github.com/Blu3Hrt/Retro_Roulette/releases) section. The zip file contains:
- `Retro Roulette.exe`: Main executable file.
- `bizhawk_server.lua`: Lua server script. Place it in the same directory as the `.exe`.
- `Lua` folder: Contains files to be placed in the Lua subfolder of the Bizhawk directory.

## Features

### Game Management
- **Add Games:** Easily add games to your list.
- **Game Interaction:** Right-click on a game to shuffle, mark as complete, rename, or set goals.
- **Rename:** Double-click to rename games.

### Session Management
- **Session Operations:** Create, save, rename, or delete game sessions.
- **Default Session:** Automatically creates and uses a default session when no other sessions are available.

### Configuration
- **Themes:** Choose between Dark and Light modes.
- **Path Setting:** Add the path for BizHawk (EmuHawk.exe).
- **Game Swap Timing:** Set the earliest and latest times for game swapping.
- **Hotkeys:** Define hotkeys for marking a game as completed.

### Shuffle Management
- **BizHawk Integration:** Launch the BizHawk executable added in the Configuration.
- **Shuffle Controls:** Start, pause, and resume game shuffling.

### Stats Tracking
- **Session Statistics:** View statistics for the entire session and individual games.
- **File Output:** Outputs game swaps and time spent to text files. (Goal tracking coming soon)
- **OBS Integration:** Useful for displaying stats through OBS.

### Twitch Integration [Experimental]
- **Channel Point Rewards:** Manage Twitch channel point rewards to pause shuffle and force game swaps.
- **Customization:** Set active status, cost, cooldown, and pause duration for rewards.

## Acknowledgements
Special thanks to the creator of *BizHawk Shuffler 2* for inspiration. Check out the original project by authorblues [here](https://github.com/authorblues/bizhawk-shuffler-2).
