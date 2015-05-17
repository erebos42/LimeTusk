# LimeTusk
Create modular and beautfiul songbooks using LilyPond and LaTeX.


## ToDo
* Implement hammer on and pull of using slurs
    * Lookahead in Tuxguitar exporter needed
* Fix slides (glissandos)
    * Lookahead in Tuxguitar exporter needed
    * \set glissandoMap = #'((0 . 0)) \glissando \unset glissandoMap. 
    * \once\override NoteColumn.glissando-skip = ##t
* Hide tied notes (built in hideSplitTiedTabNotes doesn't work)
    * hideSplitTiedTabNotes = {
          \override TabVoice.TabNoteHead.details.tied-properties.break-visibility = #all-invisible
          \override TabVoice.TabNoteHead.details.tied-properties.parenthesize = ##f
          \override TabVoice.TabNoteHead.details.repeat-tied-properties.note-head-visible = ##f
          \override TabVoice.TabNoteHead.details.repeat-tied-properties.parenthesize = ##f
      }
* Support for chorded songs based on the "songs" LaTeX package
* Generator midi (using lilypond) and link into pdf document


## Ideas
* Support for lilypond files (direct), powertab...
