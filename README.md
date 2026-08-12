# Chess Rating Grapher

A Python & Flask tool for generating `.png` chart of chess rating progress
on [Lichess.org](https://lichess.org) and [Chess.com](https://chess.com).

No API key or login is needed as it uses each site's freely accessible public data.

## Features

- Compare up to **two players** at once (support for more is planned)
- Choose game type per player: **rapid / blitz / bullet** (support for more is planned)
- Plot by **date** or by **games played**
- View the resulting chart in browser or download as PNG

## Usage

Setup:
```bash
pip install -r requirements.txt
```


Run the app:

```bash
python main.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser, fill in player details, and generate a chart.

## About

I made this for fun as I wasn't aware of a tool like it, so I'm sharing it in case anyone else wants it too.

**Author:** Eden Li ([@lovanby](https://github.com/lovanby))