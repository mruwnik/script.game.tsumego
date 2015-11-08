# Tsumego
  This is a [Kodi](http://kodi.tv/) addon that allows one to solve [tsumego](https://en.wikipedia.org/wiki/Tsumego), which are problems from the boardgame [Go](https://en.wikipedia.org/wiki/Go_%28game%29). The idea for this addon stems from the fact that I couldn't get a brower to work in Kodi and couldn't be bothered to find out more. The inspiration for this comes from [goproblems](http://www.goproblems.com). The implementation is very loosely based on the [Netwalk](http://kodi.wiki/view/Add-on:Netwalk_Game) game.

# Game play
  The goal of each problem is to end up with the best possible situation for whichever player you are controlling. Sometimes this mean killing of your enemy, sometimes just minimising your loses. When a problem loads, the cursor on the board should change colour to show whose move it is. Each problem has a predefined set of possible plays, and at least one of them should be correct. If you play all the way through a correct sequence, a green 'Solved' will be displayed on the right. If you stray of the predefined path, a red 'Off path' will be displayed. This usually means that you are wrong, as all the valid paths should have been forseen in the problem.
  
  When you first start the program, your rank will be set to 30 kyu. This can be changed in the settings. While you play, your rank will be updated to better fit your current status. Updated means that it decreases (or goes to higher kyu values) on failures, but increases (or goes toward higher dan values) when you succeed. This is saved, so you can leave the program as often as you want and not worry about losing your rank. Each successfully solved problem will slightly increase your level, while your rank will be slightly decreased each time you have to undo a move or reset the problem. Showing hints will also decrease your rank, but by more than a simple undo. Each rank modification is only done once per problem. So if you solve a problem you can undo moves or show hints without worrying that it will effect your level. On the other hand, if you fail to solve the problem flawlessly, then it won't be counted as a success. Going to the next problem doesn't count either way, so that is a simple way to cheat if you think that a problem will be too hard.

# Controls
  * Use the arrow buttons to navigate. The number keys can be used to jump to hoshi points.
  * Press enter to place a stone.
  * Press back to undo a move.
  * Press 'n' to go to the next problem
  * Press 'esc' or 'q' to exit
  * Select the restart button to restart the current problem
  * Select the 'Show solution' button to toggle hints

# Problems configuration
  Tsumego doesn't ship with default problems - that is up to the user to provide. To provide the problems, all that is needed is to point to a valid folder in the configuration, or, while the program has been started, press 'i'. If no problems have been provided, or if the program can't access them, a message will be displayed on the right side informing of the problem and how to fix it.

  All tsumego problems must be in separate \*.sgf files that each contain 1 problem in the [SGF format](http://senseis.xmp.net/?SmartGameFormat). Each SGF file should contain at least one path of play, with at least one path having a node with a comment containg the word 'RIGHT'. Any node with that comment will be viewed as meaning that the problem is solved once the player gets to it. See the problems at [goproblems.com](http://www.goproblems.com) for examples.
  
# Problems folder
  The program expects the folder with the problems to have the following format:
```
base folder >
 └ 30_kyu >
 │   └ 123123.sgf
 │   └ 4322.sgf
 │   └ [3]_30_kyu_324.sgf
 │   └ 30_kyu_3324.sgf
 │   └ random_problem.sgf
 │   (...)
 └29_kyu >
 │   └easy_problem.sgf
 │   └ 54322.sgf
 │   └[-4]_29_kyu_24.sgf
 │   └29_kyu_544.sgf
 │   └ random_problem.sgf
 │   (...)
 └ (...)
 │
 └2_dan >
 │   └423.sgf
 │   └hard_problem.sgf
 │   (...)
 │
 (...)
```
It's important that each rank has it's own folder with it's own problems. The name of each rank's folder must be of the '{number}\_{type}' format, e.g. `15_kyu`, `9_kyu`, `7_dan`, otherwise it won't be recognised. It's ok to skip ranks, as long as it's not too much. The program looks for problems around the current rank, going 3 ahead an 3 behind if it can't find anything. So, if your rank was e.g. 20 kyu, the program would look for a problem at your level, and on failure would check for 19 kyu, 18 kyu, 17 kyu, 21 kyu, 22 kyu and 23 kyu. If none of those folders could be found, or if they were all empty, an error message will be displayed with instructions.

  The problems themselves can be named however you want, as long as they end with a '.sgf'. If you have a tsumego which has been rated, you can express it in the name, which will then be displayed in the top right corner. Such names should be in the following format:
  ```[{problem rating}]_{problem rank}_{problem id}.sgf```
examples of the above would be `[+4]_3_kyu_123.sgf` or `[-9]_9_kyu_5.sgf`. The problem rating is how well you think of this problem, the rank is how hard it is, while the id is a numerical identifier of the problem. The rating can be skipped, which will result in it being set to 0.

# Where to get problems
 The SGF format is very popular, so finding game plays in that format is not hard. One thing to bear in mind is that there must be at least one path containing a comment with the string 'RIGHT' in it, otherwise that problem will be unsolvable. See [problems.py](https://github.com/mruwnik/script.game.tsumego/blob/master/resources/lib/problems.py) for some test SGFs.

 I personaly use the problems at [goproblems.com](http://www.goproblems.com), but they are copyrighted so I didn't include them here. I did however include the script I used to get them - see [go_problems.py](https://github.com/mruwnik/script.game.tsumego/blob/master/go_problems.py).


# Ideas that weren't implemented
* scale the board when the tsumego is small - won't do now, as it doesn't seem to be a problem
* show a tree of all variations - probably won't do, because it would be too slow

