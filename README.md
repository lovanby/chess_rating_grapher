README

This python & Flask tool is for generating .png file charts of player chess 
ratings on either lichess.org or Chess.com.
Currently, it can support up to two players, but this will be expanded in the
future. There are three game types selectable, rapid/blitz/bullet. More are planned 
to be added in the future as well.

No API key or log-ins are required as it uses freely accessible data from both websites.

The project requires:

pip install requests matplotlib flask

Running main.py and going to http://127.0.0.1:5000 will bring up a form to fill
in with player details.

I've just made this tool for fun as I wasn't aware of any others like it. I've 
published it in case anyone has thought the same.

Author:

Eden Li (lovanby on GitHub)