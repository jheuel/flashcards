#import "@preview/gentle-clues:1.2.0": *

#let format-cards = body => {
  set page(
    paper: "a4",
    columns: 2,
    margin: 2cm,
    numbering: "1 / 1",
    fill: auto,
  )

  set text(size: 0.7em)
  show raw: set text(size: 0.9em)

  // Get all content as elements
  let elements = if type(body) == content {
    body.children
  } else {
    (body,)
  }

  let result = ()
  let current-title = none
  let current-content = ()

  let card(title: "Question", ..args) = clue(
    title: title,
    title-weight-delta: 100,
    accent-color: rgb(23, 146, 153),
    icon: image("/assets/icons/questionmark.svg"),
    ..args,
  )

  for element in elements {
    if element.func() == heading {
      if element.depth > 2 {
        result.push(element)
        continue
      }

      // heading leve 1 or 2 finish cards
      if current-title != none {
        result.push(
          card(title: current-title)[
            #current-content.join()
          ],
        )
      }
      if element.depth == 1 {
        current-content = ()
        current-title = none
        
        result.push([
          #pagebreak(weak: true)
          #place.flush()
          #place(
            top + center,
            float: true,
            scope: "parent",
            clearance: 2em,
          )[
            #show "::": $med arrow med$
            #show heading.where(level: 1): set text(size: 1.1em, weight: "medium")
            #element
          ]
        ])
        continue
      }

      // must be depth == 2, which is a question title
      current-title = [
        #set text(size: 1em, fill: black)
        #element.body
      ]
      current-content = ()
    } else if current-title != none {
      // Collect content for current question
      current-content.push(element)
    } else {
      result.push(element)
    }
  }

  // Don't forget the last Q&A pair
  if current-title != none {
    result.push(card(title: current-title)[#current-content.join()])
  }

  result.join()
}
