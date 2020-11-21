<h2>Hanabi Copying Agent</h2>
run_game.py command line arguments:
<ul>
    <li>
        <code>-a</code>: list of agent names (baseline, random, etc.) to be used in the games
        <br>
        <code>-a baseline random</code> would have <code>BaselineAgent</code> play against <code>RandomAgent</code>
        <br>
        Default: <code>baseline baseline</code>
        <br>
        Possible agents are <code>baseline</code>, <code>random</code>, <code>advh</code> (Advanced Human), and <code>cardID</code> (Card Identifier)
    </li>
    <li>
        <code>-p</code>: number of players
        <br>
        Default: <code>2</code>
    </li>
    <li>
        <code>-c</code>: number of colors
        <br>
        Default: <code>5</code>
    </li>
    <li>
        <code>-r</code>: number of ranks
        <br>
        Default: <code>5</code>
    </li>
    <li>
        <code>-hs</code>: hand size
        <br>
        Default: <code>r</code>
    </li>
    <li>
        <code>-i</code>: number of info tokens
        <br>
        Default: <code>8</code>
    </li>
    <li>
        <code>-l</code>: number of life tokens
        <br>
        Default: <code>3</code>
    </li>
    <li>
        <code>-s</code>: random number generator seed
        <br>
        Default: <code>-1</code> (random seed)
    </li>
    <li>
        <code>-v</code>: verbosity (0 for no info, 1 for scores only, 2 for some turn info, 3 for everything)
        <br>
        Default: <code>0</code>
    </li>
    <li>
        <code>-n</code>: number of rounds played
        <br>
        Default: <code>1</code>
    </li>
</ul>

