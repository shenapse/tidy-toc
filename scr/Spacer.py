import dataclasses
import itertools
from typing import Final, Optional

import regex
from regex import Match, Pattern
from typing_extensions import Self

from Choose_from_Integers import Choose_from_Integers
from Mediator import Candidate, Choice, Mediator, Option
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Insert_Space(Choose_from_Integers):
    def __init__(
        self,
        lines: Paged_Text_Lines,
        options_max: int = 100,
        pat_need_space: Pattern = regex.compile("(?<=[a-z])[A-Z]"),
    ) -> None:
        self.lines: Paged_Text_Lines = lines
        self.pat_need_space: Pattern = pat_need_space
        self.mediator = Mediator(
            public_options=[Option.Pass.value, Option.Remove.value],
            private_options=[Option.Digit.value],
            max_page=options_max,
        )

    def get_rows_space_inserted(self) -> Paged_Text_Lines:
        """interactively insert space where a lower character is followed by an Upper character with no space between."""
        return self.choose_from_integers()

    def find_rows(self) -> list[Paged_Text_Line]:
        """find rows having strings in which a lower character is followed by an Upper character. e.g., ProbabilityTheory"""
        return [p for p in self.lines if p.test_pattern_at(self.pat_need_space)]

    def _get_where_to_insert(self, line: Paged_Text_Line) -> list[list[int]]:
        """get the list of positional indexes of line.text at which space might need to be inserted."""
        starts = list(
            itertools.chain.from_iterable(
                [[start for start in match.starts()] for match in regex.finditer(self.pat_need_space, line.text)]
            )
        )
        combinations: list[list[int]] = []
        for r in range(len(starts) + 1):
            combinations.extend([cl for c in itertools.combinations(starts, r) if (cl := list(c)) != []])
        return combinations

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """suggest new strings by which an input line might be replaced."""

        def insert_space(text: str, where_to_insert: list[int]) -> str:
            """get new text with space at specified index."""
            add = 0
            for c in where_to_insert:
                at: int = c + add
                text = text[:at] + " " + text[at:]
                add += 1
            return text

        return Candidate.to_candidate(
            [insert_space(text=line.text, where_to_insert=at) for at in self._get_where_to_insert(line)]
        )

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        """test if candidates for the line is too trivial for user to choose. If true, then the trivial choice is forced by some other method that follows."""
        # trivial cases
        return (L := len(candidates)) == 0 or L == 1

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        """decide the forced choice after candidates turn out to be trivial."""
        if (L := len(candidates)) == 0:
            return Choice(option=Option.Pass, number=0)
        elif L == 1:
            return Choice(option=Option.Digit, number=candidates[0].idx)
        raise ValueError(f"unexpected pair of {line} and {candidates}")


class Remove_Space(Choose_from_Integers):
    def __init__(
        self,
        lines: Paged_Text_Lines,
        options_max: int = 100,
        pat_spaced_double_bytes: Pattern = regex.compile("(?<=[^\x01-\x7E部章節])[ \\s]+[^\x01-\x7E]"),
    ) -> None:
        self.lines: Paged_Text_Lines = lines
        self.pat_spaced_double_bytes: Pattern = pat_spaced_double_bytes
        self.mediator = Mediator(
            public_options=[Option.Pass.value, Option.Remove.value],
            private_options=[Option.Digit.value],
            max_page=options_max,
        )

    def has_double_bytes(self, text: str) -> bool:
        return regex.search(r"[^\x01-\x7E]", text) is not None

    def get_rows_space_removed(self) -> Paged_Text_Lines:
        """interactively insert space where a lower character is followed by an Upper character with no space between."""
        return self.choose_from_integers()

    def find_rows(self) -> list[Paged_Text_Line]:
        """find rows having strings in which a space character lies between double-byte characters. e.g., 全角文字と 全角文字"""
        return [p for p in self.lines if p.test_pattern_at(self.pat_spaced_double_bytes)]

    def _get_where_to_remove(self, line: Paged_Text_Line) -> list[list[int]]:
        """get the list of positional indexes of line.text at which space might need to be inserted."""
        starts = list(
            itertools.chain.from_iterable(
                [
                    [start for start in match.starts()]
                    for match in regex.finditer(self.pat_spaced_double_bytes, line.text)
                ]
            )
        )
        combinations: list[list[int]] = []
        for r in range(len(starts)):
            combinations.extend([list(c) for c in itertools.combinations(starts, r) if c != []])
        return combinations

    def _is_trivial_candidate(self, line: Paged_Text_Line, new_text: str) -> bool:
        """check whether new_text is a worthy candidate."""
        # trivial if it is exactly the same as line
        if line.text == new_text:
            return True
        # trivial if it has digit header and has a single word part
        if line.header == line.Header.DIGIT and any(
            len(w) == 1 for i, w in enumerate(new_text.split()) if i > 0 and self.has_double_bytes(w)
        ):
            return True
        return False

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """suggest new strings by which an input line might be replaced."""

        def remove_space(text: str, where_to_remove: list[int]) -> str:
            """get new text with space at specified index."""
            add = 0
            for c in where_to_remove:
                end_first: int = c + add
                start_second = end_first + 1
                text = text[:end_first] + text[start_second:]
                add -= 1
            return text

        cands: list[str] = []
        for at in self._get_where_to_remove(line):
            new_text: str = remove_space(text=line.text, where_to_remove=at)
            if not self._is_trivial_candidate(line, new_text):
                cands.append(new_text)
        return Candidate.to_candidate(cands)

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        """test if candidates for the line is too trivial for user to choose. If true, then the trivial choice is forced by some other method that follows."""
        # trivial cases
        if (L := len(candidates)) == 0:
            return True
        if L > 1:
            # trivial if line.words consists solely of single word like '推 定 法'
            return all(len(w) == 1 for i, w in enumerate(line.words) if i > 0)
        # L==1
        return True

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        """decide the forced choice after candidates turn out to be trivial."""
        if (L := len(candidates)) == 0:
            return Choice(option=Option.Pass, number=0)
        elif L > 1:
            return Choice(option=Option.Digit, number=candidates[-1].idx)
        if L == 1:
            if candidates[0].text == "":
                return Choice(option=Option.Remove, number=0)
            else:
                return Choice(option=Option.Digit, number=candidates[0].idx)
        raise ValueError(f"unexpected pair of {line} and {candidates}")


@dataclasses.dataclass
class Header_Symbol:
    symbol: str
    appearance: int

    def __lt__(self, other: Self) -> bool:
        return self.appearance < other.appearance

    @classmethod
    def to_symbols(cls, d: dict[str, int]) -> list[Self]:
        return sorted([Header_Symbol(symbol=key, appearance=value) for key, value in d.items()], reverse=True)


class Header_Symbol_Detecter:
    pat_leading_symbol: Final[Pattern] = regex.compile("^([^\\d\\s])(?=\\s?\\d)")

    @classmethod
    def coalesce(cls, x: Optional[str]) -> str:
        return "" if x is None else x

    def __init__(self, lines: Paged_Text_Lines, header_symbol: Optional[str] = "", sep: Optional[str] = ".") -> None:
        self.mediator = Mediator(public_options=[Option.Exit.value], private_options=[Option.Digit.value])
        self.lines: Paged_Text_Lines = lines
        self.header_freq: dict[str, int] = {self.coalesce(header_symbol): 0}
        self.header_symbol: Optional[str] = self.coalesce(header_symbol)
        self.sep_freq: dict[str, int] = {self.coalesce(sep): 0}
        self.sep_symbol: Optional[str] = self.coalesce(sep)

    def detect(self) -> None:
        self.header_freq = self.get_header_symbol_frequency()
        self.header_symbol = None if (sym := self.get_header_symbol()) is None else sym.symbol
        self.sep_freq = self.get_header_sep_frequency(self.header_symbol)
        self.sep_symbol = None if (s := self.get_header_sep(self.header_symbol)) is None else s.symbol

    def _get_frequency(self, pat: Pattern) -> dict[str, int]:
        """get potential header symbol with their appearance times"""
        freq: dict[str, int] = {}
        for line in self.lines:
            hit: Optional[Match] = regex.search(pat, line.text)
            if isinstance(hit, Match):
                symbol: str = hit.group()
                freq.setdefault(symbol, 0)
                freq[symbol] += 1
        return freq

    def get_header_symbol_frequency(self) -> dict[str, int]:
        """get potential header symbol with their appearance times"""
        return self._get_frequency(self.pat_leading_symbol)

    def get_idx_symboled(self) -> list[int]:
        """get list of line.idx that hit the potential header symbol pattern"""
        return [line.idx for line in self.lines if regex.search(self.pat_leading_symbol, line.text) is not None]

    def show_header_symbols(self, symbols: list[Header_Symbol]) -> None:
        if len(symbols) > 0:
            print("\n")
            for i, symbol in enumerate(symbols):
                print(f"{i} | {symbol.symbol} appearance times = {symbol.appearance}")
            print("\n")
        else:
            print("no header symbols are detected.")

    def _get_symbol(self, symbols: list[Header_Symbol]) -> Optional[Header_Symbol]:
        if len(symbols) == 0:
            return
        self.mediator.explain()
        self.show_header_symbols(symbols)
        user_input, _ = self.mediator.get_user_input(default_value="0", domain=range(len(symbols)))
        choice = self.mediator.interpret(user_input=user_input)
        match choice.option:
            case Option.Exit:
                return
            case Option.Digit:
                return symbols[choice.number]
            case _:
                raise Exception(f"unknown choice type {choice.option}.")

    def get_header_symbol(self) -> Optional[Header_Symbol]:
        symbols = Header_Symbol.to_symbols(self.get_header_symbol_frequency())
        if len(symbols) > 0:
            print("choose header symbol.")
        return self._get_symbol(symbols)

    def get_header_sep_frequency(self, header_symbol: Optional[str]) -> dict[str, int]:
        pat_lead: str = "(?<=^\\s?\\d+)" if header_symbol is None else f"(?<=^{header_symbol}\\s?\\d+)"
        pat: Pattern = regex.compile(f"{pat_lead}[^\\s\\d]")
        return self._get_frequency(pat)

    def get_header_sep(self, header_symbol: Optional[str]) -> Optional[Header_Symbol]:
        symbols = Header_Symbol.to_symbols(self.get_header_sep_frequency(header_symbol))
        if len(symbols) > 0:
            print("choose separator of digits in header.")
        return self._get_symbol(symbols)


class Header_Aligner(Choose_from_Integers):
    @classmethod
    def coalesce(cls, x: Optional[str]) -> str:
        return "" if x is None else x

    def __init__(
        self,
        lines: Paged_Text_Lines,
        ignore: set[str] = set(),
        sep_possible: list[str] = [",", "\\."],
        sep: Optional[str] = None,
        header_symbol: Optional[str] = None,
    ) -> None:
        self.lines: Paged_Text_Lines = lines
        self.mediator = Mediator(
            public_options=[Option.Pass.value, Option.Exit.value], private_options=[Option.Digit.value]
        )
        self.detecter = Header_Symbol_Detecter(lines=lines, header_symbol=header_symbol, sep=sep)
        self.header_symbol: str = self.coalesce(header_symbol)
        self.sep: str = self.coalesce(sep)
        self.ignore: set[str] = ignore
        self.sep_possible: list[str] = sep_possible
        self.pats_align: list[Pattern] = [self._get_pat_align(), self._get_pat_align(include_possible_sep=False)]
        self.pat_well_aligned: Pattern = self._get_pat_well_aligned()
        self.pat_header_symbol: Pattern = self._get_pat_header_symbol()
        self.pat_sep_possible: Pattern = self._get_pat_sep_possible()
        self.pat_digit_place_undecidable: Pattern = self._get_pat_digit_place_undecidable()
        # self.pat_replace_header: Pattern = regex.compile(f"^[{regex.compile(self.header_symbol)}]")
        # pat_replace_sep: Final[Pattern] = regex.compile("")

    def detect_symbols(self) -> None:
        def coalesce(x: Optional[str]) -> str:
            return "" if x is None else x

        self.detecter.detect()
        self.header_symbol = coalesce(self.detecter.header_symbol)
        self.sep = coalesce(self.detecter.sep_symbol)
        self.pats_align = [self._get_pat_align(), self._get_pat_align(include_possible_sep=False)]
        self.pat_well_aligned = self._get_pat_well_aligned()
        self.pat_header_symbol = self._get_pat_header_symbol()
        self.pat_sep_possible = self._get_pat_sep_possible()
        self.pat_digit_place_undecidable = self._get_pat_digit_place_undecidable()

    def is_ignorable(self, text: str) -> bool:
        return any(text.lower().startswith(w.lower()) for w in self.ignore)

    def _get_pat_well_aligned(self) -> Pattern:
        sep: str = regex.escape(self.sep)
        return regex.compile(f"^{(regex.escape(self.header_symbol))}[\\d{sep}]+\\s[^\\d\\s{sep}]")

    def is_aligned(self, line: Paged_Text_Line) -> bool:
        """test wether header consists of header symbol + ( digit + sep )* + other string"""
        return regex.search(self.pat_well_aligned, line.text) is not None

    def _get_pat_header_symbol(self) -> Pattern:
        return regex.compile(f"^{(regex.escape(self.header_symbol))}")

    def _get_pat_sep_possible(self) -> Pattern:
        return regex.compile(f"[{''.join(self.sep_possible)}]+")

    def _get_pat_digit_place_undecidable(self) -> Pattern:
        chrs: str = "".join(self.sep_possible + [regex.escape(self.sep), "\\s", "\\d"])
        return regex.compile(f"(?<=^{regex.escape(self.header_symbol)}[{chrs}]+)\\d[^{chrs}]")

    def replace_header_symbol(self, text: str) -> str:
        return regex.sub(self.pat_header_symbol, self.header_symbol, text)

    def replace_sep(self, text: str) -> str:
        return regex.sub(self.pat_sep_possible, self.sep, text)

    def _get_pat_align(self, include_possible_sep: bool = True) -> Pattern:
        # unique detected header symbols
        header_symbols: list[str] = list(set([regex.escape(key) for key in self.detecter.header_freq]))
        # make this list non-empty to simply construct pattern
        if header_symbols == []:
            header_symbols.append("")
        # possible characters in header except header symbol
        characters_header: list[str] = [regex.escape(self.sep)] + ["\\d", "\\s"]
        if include_possible_sep:
            characters_header.extend(self.sep_possible)
        precede: str = header_symbols[0] if len(header_symbols) == 1 else f"[{''.join(header_symbols)}]"
        return regex.compile(f"(?<=^{precede})[{''.join(characters_header)}]+")

    def _get_aligned(self, text: str) -> list[str]:
        als: set[str] = set()
        for pat in self.pats_align:
            hit: Optional[Match] = regex.search(pat, text)
            if isinstance(hit, Match):
                end: int = hit.end()
                al: str = (regex.sub("\\s", "", text[:end])).strip() + " " + text[end:].strip()
                als.add(al)
            else:
                als.add(text)
        return list(als)

    def align_header(self) -> Paged_Text_Lines:
        return self.choose_from_integers()

    def find_rows(self) -> list[Paged_Text_Line]:
        return [
            self.lines[i]
            for i in self.detecter.get_idx_symboled()
            if not self.is_ignorable(self.lines[i].text) and not self.is_aligned(self.lines[i])
        ]

    def _get_raw_candidates(self, text: str) -> list[str]:
        """get possible pattern of candidates. replace_header x replace_sep"""
        cands: set[str] = set()
        als: list[str] = self._get_aligned(text)
        for al in als:
            init: list[str] = [al, self.replace_header_symbol(al)]
            for cand in init:
                cands.add(cand)
                cands.add(self.replace_sep(cand))
        return list(cands)

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        cands: set[str] = set()
        for al in self._get_aligned(line.text):
            for cand in self._get_raw_candidates(al):
                if not self._is_worthless_candidate(line, cand):
                    cands.add(cand)
        return Candidate.to_candidate(sorted(cands))

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        if self._is_digit_place_undecidable(line):
            return False
        return len(candidates) == 1

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        if len(candidates) == 1:
            return Choice(option=Option.Digit, number=candidates[0].idx)
        raise ValueError(f"unexpected pair of {line} and {candidates}")

    def _is_worthless_candidate(self, line: Paged_Text_Line, new_text: str) -> bool:
        if self.is_ignorable(line.text) or len(new_text) == 0 or new_text == line.text:
            return True
        return False

    def _on_ignore(self, line: Paged_Text_Line):
        raise NotImplementedError

    def _is_digit_place_undecidable(self, line: Paged_Text_Line) -> bool:
        """test if line.text has sentence that starts with digit just after header. e.g., 1.3 2stage regression"""
        return regex.search(self.pat_digit_place_undecidable, line.text) is not None
