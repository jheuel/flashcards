# Typst Flashcards for [Anki](https://apps.ankiweb.net/)

**Syntax:**

1) First level headings generate new decks.
2) Second level headings define questions.
3) Content between headings become answers.

## Usage

Build the pdf with

``` sh
typst compile deck.typ
```

or generate the Anki deck with

``` sh
uv run generate.py deck.typ
```

The Python script

- Splits the input into decks based on first-level headings
- Converts each deck into individual cards using second-level headings
- Generates SVG images for question and answer fields
- Creates Anki notes from the SVG images
- Builds a deck file `DECKNAME.apkg` for importing into Anki
- Adds Anki IDs as labels to headings in the source file for synchronization

## Example: One Card

``` typst
// some common settings for Anki and PDF
#import "common.typ": *
#show: style

// format cards for the PDF document
#import "cards.typ": *
#show: format-cards

= Example deck name

== This must be a question?!
This is the corresponding answer.
```

## Example: 20 Belter language flashcards

I let a Claude generate a few flashcards about the [Belter
language](https://en.wikipedia.org/wiki/Belter_Creole) from the TV show [The
Expanse](https://en.wikipedia.org/wiki/The_Expanse_(TV_series)).
The output can be found in [`examples/expanse.typ`](examples/expanse.typ).

The rendered pdf document is available at
[`examples/expanse.pdf`](examples/expanse.pdf), and a complete Anki
deck can be found at [`examples/decks/The
Expanse.apkg`](examples/decks/The%20Expanse.apkg).
Below, you find an example card: A question above a separating horizontal line and the answer below.
The SVGs are transparent and you can color the background in Anki.

### SVG

<img src="https://github.com/user-attachments/assets/281c8a80-ea12-454b-a4d4-3b682201032d" style="width: 600px; height: auto;" alt="Image" />

<img src="https://github.com/user-attachments/assets/38f1e7b4-f710-48e3-a0bf-3c1aee4e472b" style="width: 600px; height: auto;" alt="Image" />


### PDF

<img src="https://github.com/user-attachments/assets/b040555e-a5fc-4652-b83c-e28aac3c98f8" style="width: 600px; height: auto;" alt="Image" />

### Anki

<img src="https://github.com/user-attachments/assets/0a83005a-7108-4eb6-aefc-5fc6d7a78d80" style="width: 600px; height: auto;" alt="Image" />

<img src="https://github.com/user-attachments/assets/5f2a475b-a76f-4a5c-aed5-e081939707fb" style="width: 600px; height: auto;" alt="Image" />
