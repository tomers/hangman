import random
import typer
from typing_extensions import Annotated
from typing import Optional, Generator, Tuple
from pathlib import Path
from itertools import cycle
from enum import Enum

app = typer.Typer()


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
    def message(self):
        return {
            GuessResult.INVALID: "Invalid guess. Please try again",
            GuessResult.CORRECT: "Correct guess",
            GuessResult.INCORRECT: "Incorrect guess",
            GuessResult.DUPLICATE: "Duplicate guess (already guessed)",
            GuessResult.WORD_COMPLETE: "Word found!",
        }[self]


class GuessedWord:
    def __init__(self, word: str) -> None:
        assert len(word) > 0
        self._word = word.lower()
        self._guessed = [False] * len(word)
        self._found_letters = set()

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
        return result

    def __str__(self) -> str:
        return "".join(
            char if guessed else "_" for char, guessed in zip(self._word, self._guessed)
        )


class Player:
    def __init__(self, name: str):
        self._name = name
        self._score = 0

    def __str__(self) -> str:
        return f"<{self._name} (score: {self._score})>"

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
        print(f"Word: {gw}; Players: {self._players}")

    def play(self):
        print("Welcome to Hangman!")
        for i, word in enumerate(self._word_bank.words, 1):
            print(f"\nRound #{i}/{self._word_bank.word_count}")
            gw = GuessedWord(word)
            self.print_status(gw)
            for player in self._players.iter():
                while True:
                    print(f"{player.name}, please select a letter")
                    letter = input()
                    res, score = gw.guess(letter)
                    player.add_score(score)
                    print(res.message)
                    if res in {
                        GuessResult.CORRECT,
                        GuessResult.INCORRECT,
                        GuessResult.WORD_COMPLETE,
                    }:
                        self.print_status(gw)
                        break
                if res == GuessResult.WORD_COMPLETE:
                    break

        print("\nGame over!")
        winners = self._players.winners
        if len(winners) == 1:
            print(f"{winners[0].name} wins with score {winners[0].score}!")
        else:
            print("It's a tie! Winners:")
            for winner in winners:
                print(f"{winner.name} (score: {winner.score})")


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
