#import "@preview/muchpdf:0.1.1": muchpdf
#import "@preview/gentle-clues:1.2.0": *

#let style = body => {
  set text(size: 0.9em)

  set text(font: "STIX Two Text")
  show math.equation: it => {
    if not it.block {
      return it
    }
    set text(font: "STIX Two Math", fill: rgb("#47999b"))
    it
  }

  show raw: set text(size: 0.75em)

  set page(
    width: 10cm,
    height: auto,
    margin: (x: 5mm, y: 5mm),
    fill: none,
  )

  set par(justify: false)

  body
}

#let pdf = path => {
  set align(center)
  muchpdf(read(path, encoding: none))
}

#let hbar = (sym.wj, move(dy: -0.08em, strike(offset: -0.55em, extent: -0.05em, sym.planck)), sym.wj).join()
