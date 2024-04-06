
# Retro Roulette

## Overview
*Retro Roulette* is a gaming management and streaming tool that enhances the gaming experience with game shuffling, session management, and Twitch integration. This application is inspired by *BizHawk Shuffler 2* and is perfect for gamers and streamers who love variety and interaction.

## Installation
Download the latest release from the [Releases](https://github.com/Blu3Hrt/Retro_Roulette/releases) section. The zip file contains:
- `Retro Roulette.exe`: Main executable file.
- `bizhawk_server.lua`: Lua server script. Place it in the same directory as the `.exe`.
- `Lua` folder: Contains files to be placed in the Lua subfolder of the Bizhawk directory.

## Getting Started
### Initial Configuration
1. **Set BizHawk Path:** In the Configurations tab, set the path to your BizHawk installation.
2. **Shuffle Intervals:** Define minimum and maximum shuffle intervals. These intervals determine how often games will swap during a shuffle session.
3. **Hotkey Setup:** Optionally, change the global hotkey for marking and unmarking a game as complete.
4. **Save Configurations:** Remember to save any changes you make in the configurations.

### Game Management
1. **Add Games:** In the Game Management tab, add the games you want to include in the shuffle.
2. **Customize Game Names and Goals:** Rename games as desired and set personal goals for completion.

### Shuffle Management
1. **Launch BizHawk:** Click 'Launch BizHawk' to start the emulator with the necessary Lua script.
2. **Start and Manage Shuffle:** Begin the game shuffle. Use 'Pause Shuffle' to stick to the current game (timer continues running) and 'Resume Shuffle' to continue where you left off.
3. **Stats Tracking:** Access statistics in the Stats tab and check the files written in the Stats subdirectory.

### Session Management
- **Manage Sessions:** Use the buttons to create new sessions, save the current session with a new name, rename, or delete sessions.
- **View Session Details:** Easily view details of the currently selected session, including the number of games, completed games, swaps, and session time.
- **Switch Between Sessions:** Use the dropdown menu to switch between different sessions.

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
- **Path Setting:** Add the path for BizHawk (Be sure to save configuration before launching BizHawk.).
- **Game Swap Timing:** Set the earliest and latest times for game swapping.
- **Hotkeys:** Define hotkeys for marking a game as completed.

### Shuffle Management
- **BizHawk Integration:** Launch the BizHawk executable via the path added in the Configuration. 
- **Shuffle Controls:** Start, pause, and resume game shuffling.

### Stats Tracking
- **Session Statistics:** View statistics for the entire session and individual games.
- **File Output:** Outputs game swaps and time spent to text files. (Goal tracking coming soon)
- **OBS Integration:** Useful for displaying stats through OBS.

### Twitch Integration [Experimental]
- **Channel Point Rewards:** Manage Twitch channel point rewards to pause shuffle and force game swaps.
- **Customization:** Set active status, cost, cooldown, and pause duration for rewards.

### Twitch Integration
1. **Twitch Connection:** Sign in to Twitch and manage channel point rewards for pausing shuffles and forcing game swaps, enhancing viewer interaction.

## Using with OBS

For streamers, here are some tips for integrating Retro Roulette with OBS:

- **Full Screen Mode:** Play in full screen to maintain a consistent capture size, which is especially helpful if you're not familiar with advanced OBS settings.
- **Window Capture:** If you do use windowed mode, set up a window capture source for consistent streaming quality across different games.
- **Disable Messages:** In Retro Roulette, go to `View` and uncheck `Display Messages` to prevent save/load messages from appearing during your stream.



## BizHawk Compatibility
Retro Roulette has been tested with [BizHawk version 2.9.1](https://tasvideos.org/BizHawk/ReleaseHistory#Bizhawk291). Ensure you have this version installed for optimal performance and compatibility.

## System Requirements

- **Operating System:** Windows (Tested on Windows 11)


## Acknowledgements
Special thanks to the creator of *BizHawk Shuffler 2* for inspiration. Check out the original project by authorblues [here](https://github.com/authorblues/bizhawk-shuffler-2).


## Development Status

This project is in its early stages, and as a novice programmer, I am continually learning and improving the codebase. The current focus is on functionality, with plans to refactor for cleaner and more efficient code over time. Contributions and suggestions for improvement are welcome!

## Contact Information

Feel free to reach out to me with questions, feedback, or suggestions for Retro Roulette.

- **Twitter:** [@Blu3Hrt](https://twitter.com/Blu3Hrt)
- **Email:** [emails@blu3hrt.xyz](mailto:emails@blu3hrt.xyz)
- **Twitch:** [blu3hrt's Channel](https://twitch.tv/blu3hrt)
