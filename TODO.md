# TODO

## launcher
- give user option to update with more / less cleaning
    - option for update with stash -- call git stash push/pop before/after update, e.g. we have to track some settings and if ppl change them, updates kill it
        - alternatively, have the backend check out a local branch for everyone and merge updates in. but this option gets heavy on tech, though could in theory be ideal, i suspect this has too many ways to break in such a way that requires manual git intervention, which in the cxt of my end user friends, means it's bricked until I get to it. prob a bad idea
    - option to update from fresh
        - warn the user and be clear this is kinda a nuclear option, but this should basically kill the whole minecraft install other than saves/ (anything else? i think that's it). sometimes people get in a bad state where e.g. there's more untracked mods in the mods folder breaking things, and the launcher currently tends to ignore untracked files

- URGENT migrate IP option
    - any mod that needs to save per-world client side data does so for servers by keying on the IP. well, I don't have a domain name so my IP can change. in fact, I need to change it to switch to ethernet, (which i shouldve done from the start).
    - the #1 most important example of this, and maybe only that matters, is the map data.
        - world map can't be reset -- we spend so much time exploring on it, to have that progress erased is a real game killer.
        - second is the map's waypoints. xaero makes both these map mods, not sure which holds waypoints, bc they both show them.
    - so, we need to:
        - find each instance in the files of this important client side data keyed by the IP
        - figure out how and where to replace w the new IP s.t. the data transfers
        - add a button in launcher "migrate IP" with text fields 'old IP' and 'new IP' that will carry this out

- detect launcher update
    - hash the launcher exe before and after update, and pop up a message for the user
    - by nature of that, this one's for the windows users, as with some other things in the launcher the mac/linux launcher dont hand hold quite as much bc its assumed anyone using those can figure things out more / most are on windows
    - but: idk how making a windows shortcut works, i.e., if a desktop shortcut points to the exe,  which must stay in the dir it ships in, and the exe changes, will the shortcut update? id think so but windows is stupid so nothing surprises me. if so, helping user manage the shortcut and allow the launcher to auto update itself would be great.

- BLOCKED combine map data 
    - we each have our own world maps with the areas we've explored. ideally, i want anyone to be able to push their map data / download the latest map data, s.t. we all have all of the combined explored areas shown on our map. waypoints can stay individual. 
        - first need to develop a way to merge the map data by reverse engineering the map data format. i assume that shouldn't be crazy hard
        - this also depends on setting up the server's website, because I'm not exposing an ssh port and not currently requiring a vpn.
            - so this is BLOCKED on getting the server home page set up w a cloudflare tunnel, which is a task for another repo, so for your concern we are blocked.

## game
- fix gun recipes
    - the gun mod (tacz) is still not in because their recipe format changed. was having trouble fixing it..


