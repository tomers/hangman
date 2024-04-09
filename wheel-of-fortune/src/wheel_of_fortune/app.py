import random
from enum import Enum
from itertools import cycle
from pathlib import Path
from typing import Generator
from typing import Optional
from typing import Tuple

import typer
from rich import print
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Prompt
from typing_extensions import Annotated

app = typer.Typer()
console = Console()

POSITIVE_STYLE = "green"
NEGATIVE_STYLE = "red"


class WordBank:
    def __init__(
        self, words_file: Optional[Path] = None, num_words: Optional[int] = None
    ):
        if words_file is None:
            words_file = Path(__file__).parent.parent.parent.joinpath(
                "assets/words.txt"
            )
        assert words_file.exists()
        self._words = self.words_sample(words_file, num_words)

    @property
    def word_count(self):
        return len(self._words)

    @property
    def words(self) -> Generator[str, None, None]:
        yield from self._words

    @staticmethod
    def words_sample(words_file: Path, num_words: Optional[int]):
        words = words_file.read_text().splitlines()
        if num_words is None:
            random.shuffle(words)
            return words
        return random.sample(words, k=num_words)


class GuessResult(Enum):
    INVALID = 1
    CORRECT = 2
    INCORRECT = 3
    DUPLICATE = 4
    WORD_COMPLETE = 5

    @property
    def message(self) -> Tuple[str, str]:
        return {
            GuessResult.INVALID: ("Invalid guess. Please try again", NEGATIVE_STYLE),
            GuessResult.CORRECT: ("Correct guess", POSITIVE_STYLE),
            GuessResult.INCORRECT: ("Incorrect guess", NEGATIVE_STYLE),
            GuessResult.DUPLICATE: (
                "Duplicate guess (already guessed)",
                NEGATIVE_STYLE,
            ),
            GuessResult.WORD_COMPLETE: ("Word found!", POSITIVE_STYLE),
        }[self]


class GuessedWord:
    def __init__(self, word: str) -> None:
        assert len(word) > 0
        self._word = word.lower()
        self._guessed = [False] * len(word)
        self._found_letters = set()
        self._used_letters = set()

    def guess(self, letter: str) -> Tuple[GuessResult, int]:
        if len(letter) != 1 or not letter.isalpha():
            return GuessResult.INVALID, 0
        letter = letter.lower()
        if letter in self._found_letters:
            return GuessResult.DUPLICATE, 0
        result = GuessResult.INCORRECT, 0
        for i, char in enumerate(self._word):
            if char == letter:
                self._guessed[i] = True
                self._found_letters.add(letter)
                score = self._word.count(letter)  # number of occurances
                result = GuessResult.CORRECT, score
        if all(self._guessed):
            result = GuessResult.WORD_COMPLETE, score
        self._used_letters.add(letter)
        return result

    def __str__(self) -> str:
        word = "".join(
            char if guessed else "-" for char, guessed in zip(self._word, self._guessed)
        )
        used = ", ".join(sorted(self._used_letters)) if self._used_letters else "None"
        return f"Word: {word} | Used: {used}"


class Player:
    def __init__(self, name: str):
        self._name = name
        self._score = 0

    def __str__(self) -> str:
        return f"{self._name} score: {self._score}"

    def add_score(self, score: int):
        self._score += score

    @property
    def name(self) -> str:
        return self._name

    @property
    def score(self) -> int:
        return self._score


class Players:
    def __init__(self) -> None:
        self._players = [Player("Player 1"), Player("Player 2")]

    def iter(self):
        return cycle(self._players).__iter__()

    def __str__(self) -> str:
        return ", ".join(str(player) for player in self._players)

    @property
    def winners(self) -> list[Player]:
        by_score = sorted(self._players, key=lambda p: p.score, reverse=True)
        max_score = by_score[0].score
        return [p for p in by_score if p.score == max_score]


class GamePlay:
    def __init__(self, words_file: Path, num_rounds: Optional[int] = None):
        self._word_bank = WordBank(words_file=words_file, num_words=num_rounds)
        self._players = Players()

    def print_status(self, gw):
        print(Padding(f"{gw}", (1, 1), style="on blue", expand=False))
        print(f"{self._players}")

    def play(self):
        print(Panel.fit(":game_die: Welcome to Hangman! :game_die:"))
        for i, word in enumerate(self._word_bank.words, 1):
            print(Panel.fit(f"Round #{i}/{self._word_bank.word_count}"))
            gw = GuessedWord(word)
            self.print_status(gw)
            for player in self._players.iter():
                while True:
                    letter = Prompt.ask(f"[b]{player.name}[/b], please select a letter")
                    res, score = gw.guess(letter)
                    player.add_score(score)
                    console.print(res.message[0] + "\n", style=res.message[1])
                    if res in {
                        GuessResult.CORRECT,
                        GuessResult.INCORRECT,
                        GuessResult.WORD_COMPLETE,
                    }:
                        self.print_status(gw)
                        break
                if res == GuessResult.WORD_COMPLETE:
                    break

        title = "Game over :partying_face:"
        winners = self._players.winners
        if len(winners) == 1:
            subtitle = f":1st_place_medal: {winners[0].name} wins :1st_place_medal:"
        else:
            subtitle = "It's a tie! :people_wrestling:"
        text = "\n".join(f"{winner.name} (score: {winner.score})" for winner in winners)
        print(Panel.fit(text, title=title, subtitle=subtitle))


@app.command()
def play(
    words_file: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    num_rounds: Annotated[int, typer.Option(min=1)] = None,
):
    gp = GamePlay(num_rounds=num_rounds, words_file=words_file)
    gp.play()


if __name__ == "__main__":
    app()
