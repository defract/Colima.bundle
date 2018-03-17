#What is Colima?

Combined Library Metadata Agent (Colima) in combination with [Absolute Series Scanner (ASS)](https://github.com/ZeroQI/Absolute-Series-Scanner/ "Absolute Series Scanner (ASS)") allows you to have movies and tv shows within the same library, something that Plex sadly not supports out of the box. Common scenarios to use this agent for are documentaries, western and Japanese animation libraries.

Colima will look for a unique identificator to distinguish movies from tv shows. The agent pulls data from TheMovieDB for all movies it can find this way. TV Shows are entirely ignored by Colima itself and instead are passed as fallback to the native Plex TVDB agent. 

The code is mostly justed based on the Plex implementation of TheMovieDb on [github.com](https://github.com/plexinc-agents/TheMovieDB.bundle "github.com").

##Download

Download: https://github.com/defract/Colima.bundle/archive/master.zip
Source: https://github.com/defract/Colima.bundle

##Examples

I always like to see results, so here are two mockups of how a library could look like with Colima (created by using fake files).

**Documentaries Library**
![](https://abload.de/img/doculibh3k7l.jpg "")

**Animation Library**
![](https://abload.de/img/animationlibphkaq.jpg "")

##Where is the catch?

As already pointed out, Plex does not natively support movies within a tv show library. Putting movies into the tv show library means they will get seasons, some of their data (writers and directors) are shown differently from native movie libraries. Also, all movies within a tv show library are counted as tv shows for obvious reasons.

#Installation

1. Find out where your Plex installation is located at, see [Plex help article](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder- "Plex help article").
2. Install [Absolute Series Scanner (ASS)](https://github.com/ZeroQI/Absolute-Series-Scanner/ "Absolute Series Scanner (ASS)") 
3. Download and copy the unzipped Colima.bundle into the Plug-ins folder of your installation

A Plex server restart might be required for the Agent to appear.

#Configuration

Create a TV Show library in the language of your choice

![](https://abload.de/img/config016arzj.jpg "")

Movies and TV Shows have to be in separate folders. Ensure that movies are within a folder with a unique name that will not appear in a movie/show title.

![](https://abload.de/img/config02yeo1c.jpg "")

Use Absolute Series Scanner (ASS) to create the entries within Plex. Add the folder name to the movie identificator field (only a single value is allowed).

![](https://abload.de/img/config03cgs5h.jpg "")

#Notes
* currently this has only been tested on windows and Unraid (Linux)
* if your primary interest is Anime, you might want to check out the awesome [HAMA](https://forums.plex.tv/discussion/77636/release-http-anidb-metadata-agent-hama/p1 "HAMA"), it offers far greater capabilities in this regard

#Acknowledgements

Special thanks to ZeroQI for ASS/HAMA, I wouldn't have bothered to make my own thing without them.