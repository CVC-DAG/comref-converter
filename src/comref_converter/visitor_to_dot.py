"""The Common Optical Music Recognition Framework (COMReF) toolset.

Convert MTN representation into DOT.

Copyright (C) 2023, Pau Torras <ptorras@cvc.uab.cat>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Iterable

import pydot

from .mtn import ast as AST


class VisitorToDOT(AST.Visitor):
    """Implements conversion to a model-readable sequence."""

    def __init__(self) -> None:
        self.graph = pydot.Dot("MTN_score", graph_type="digraph")
        self.current_id = 0

    def _bless(self) -> str:
        """Give new id to node."""
        current = f"Node{self.current_id}"
        self.current_id += 1

        return current

    def _create_edge(self, node_a: pydot.Node, node_b: pydot.Node) -> None:
        edge = pydot.Edge(node_a.get_name(), node_b.get_name())
        self.graph.add_edge(edge)

    def _create_node(self, label: str) -> pydot.Node:
        node = pydot.Node(self._bless(), label=label)
        self.graph.add_node(node)

        return node

    def _create_token_node(self, label: str) -> pydot.Node:
        node = pydot.Node(self._bless(), label=label)
        node.set_shape("rect")
        self.graph.add_node(node)

        return node

    def _edge_iterable(
        self,
        obj: Iterable[AST.SyntaxNode | None],
        parent: pydot.Node,
    ) -> None:
        """Process all child elements in an iterable."""
        for child in obj:
            if child is not None:
                child_node = child.accept(self)
                self._create_edge(parent, child_node)

    def _edge_token(self, node: AST.SyntaxNode, parent: pydot.Node) -> None:
        """Accept node and add it as a child to the current parent."""
        child_node = node.accept(self)
        self._create_edge(parent, child_node)

    def visit_ast(self, root: AST.SyntaxNode) -> str:
        """Perform conversion of an MTN tree into a set of JSON-like dictionaries.

        Parameters
        ----------
        root: AST.SyntaxNode
            Any subtree to convert to dictionaries.

        Returns
        -------
        Dict
            Set of dictionaries with the MTN tree in JSON-like format.
        """
        self.graph = pydot.Dot("MTN_score", graph_type="digraph")
        node = root.accept(self)
        self.graph.add_node(node)

        return self.graph.to_string()

    def visit_score(self, score: AST.Score) -> pydot.Node:
        """Perform visiting operation on Score node."""
        score_node = self._create_node(f"Score\n{score.score_id}")
        self._edge_iterable(score.measures, score_node)

        return score_node

    def visit_note(self, note: AST.Note) -> pydot.Node:
        """Perform visiting operation on Note node."""
        note_node = self._create_node("Note")

        self._edge_token(note.notehead, note_node)
        self._edge_iterable(note.dots, note_node)
        self._edge_iterable(note.accidentals, note_node)
        self._edge_iterable(note.modifiers, note_node)

        return note_node

    def visit_toplevel(self, toplevel: AST.TopLevel) -> pydot.Node:
        """Perform visiting operation on TopLevel node."""

        # Should never be called here really
        return pydot.Node()

    def visit_token(self, token: AST.Token) -> pydot.Node:
        """Perform visiting operation on Token node."""

        keyvals = [
            (
                f"{str(k.value) if hasattr(k, 'value') else str(k)}: "
                f"{str(v.value) if hasattr(v, 'value') else str(v)}"
            )
            for k, v in token.modifiers.items()
        ]
        return self._create_token_node(
            "\n".join([token.token_type.value, str(token.position), *keyvals])
        )

    def visit_chord(self, chord: AST.Chord) -> pydot.Node:
        """Perform visiting operation on Chord node."""
        chord_node = self._create_node(
            f"Chord\nDelta: {chord.delta.numerator} / {chord.delta.denominator}"
        )

        if chord.stem is not None:
            self._edge_token(chord.stem, chord_node)
        self._edge_iterable(chord.notes, chord_node)

        return chord_node

    def visit_rest(self, rest: AST.Rest) -> pydot.Node:
        """Perform visiting operation on Rest node."""
        rest_node = self._create_node(
            f"Rest\nDelta: {rest.delta.numerator} / {rest.delta.denominator}"
        )

        self._edge_token(rest.rest_token, rest_node)
        self._edge_iterable(rest.dots, rest_node)
        self._edge_iterable(rest.modifiers, rest_node)

        return rest_node

    def visit_note_group(self, note_group: AST.NoteGroup) -> pydot.Node:
        """Perform visiting operation on NoteGroup node."""
        note_group_node = self._create_node(
            f"Note Group\n"
            f"Delta: {note_group.delta.numerator} / {note_group.delta.denominator}"
        )

        self._edge_iterable(note_group.children, note_group_node)
        self._edge_iterable(note_group.appendages, note_group_node)

        return note_group_node

    def visit_attributes(self, attributes: AST.Attributes) -> pydot.Node:
        """Perform visiting operation on Attributes node."""
        attributes_node = self._create_node(
            f"Attributes\n"
            f"Delta: {attributes.delta.numerator} / {attributes.delta.denominator}"
        )

        for x in range(1, attributes.nstaves + 1):
            subnode = self._create_node(f"STAFF {x}")
            self._create_edge(attributes_node, subnode)

            curr_key = attributes.key[x]
            if curr_key is not None:
                self._edge_token(curr_key, subnode)

            curr_clef = attributes.clef[x]
            if curr_clef is not None:
                self._edge_token(curr_clef, subnode)

            curr_timesig = attributes.timesig[x]
            if curr_timesig is not None:
                self._edge_token(curr_timesig, subnode)

        return attributes_node

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> pydot.Node:
        """Perform visiting operation on TimeSignature node."""
        timesig_node = self._create_node("Time Signature")

        if time_signature.time_symbol is not None:
            self._edge_token(time_signature.time_symbol, timesig_node)
        if time_signature.compound_time_signature is not None:
            self._edge_iterable(time_signature.compound_time_signature, timesig_node)

        return timesig_node

    def visit_key(self, key: AST.Key) -> pydot.Node:
        """Perform visiting operation on Key node."""
        key_node = self._create_node("Key")

        if key.naturals is not None:
            self._edge_iterable(key.naturals, key_node)
        if key.accidentals is not None:
            self._edge_iterable(key.accidentals, key_node)

        return key_node

    def visit_clef(self, clef: AST.Clef) -> pydot.Node:
        """Perform visiting operation on Clef node."""
        clef_node = self._create_node("Clef")

        if clef.clef_token is not None:
            self._edge_token(clef.clef_token, clef_node)

        return clef_node

    def visit_direction(self, direction: AST.Direction) -> pydot.Node:
        """Perform visiting operation on Direction node."""
        direction_node = self._create_node(
            f"Direction\n"
            f"Delta: {direction.delta.numerator} / {direction.delta.denominator}"
        )

        self._edge_iterable(direction.directives, direction_node)

        return direction_node

    def visit_measure(self, measure: AST.Measure) -> pydot.Node:
        """Perform visiting operation on Measure node."""
        measure_node = self._create_node(
            f"Measure\nPart: {measure.part_id}\nID: {measure.measure_id}"
        )

        self._edge_iterable(
            ([measure.left_barline] if measure.left_barline is not None else [])
            + measure.elements
            + ([measure.right_barline] if measure.right_barline is not None else []),
            measure_node,
        )

        return measure_node

    def visit_barline(self, barline: AST.Barline) -> pydot.Node:
        """Perform visiting operation on Barline node."""
        barline_node = self._create_node("Barline")

        self._edge_iterable(barline.barline_tokens, barline_node)
        self._edge_iterable(barline.modifiers, barline_node)

        return barline_node

    def visit_tuplet(self, tuplet: AST.Tuplet) -> pydot.Node:
        """Perform visiting operation on Tuplet node."""
        tuplet_node = self._create_node("Tuplet")

        if tuplet.number is not None:
            self._edge_token(tuplet.number, tuplet_node)
        self._edge_token(tuplet.tuplet, tuplet_node)

        return tuplet_node

    def visit_numerator(self, numerator: AST.Numerator) -> pydot.Node:
        """Perform visiting operation on Numerator node."""
        numerator_node = self._create_node("Numerator")

        self._edge_iterable(numerator.digits_or_sum, numerator_node)

        return numerator_node

    def visit_denominator(self, denominator: AST.Denominator) -> pydot.Node:
        """Perform visiting operation on Denominator node."""
        denominator_node = self._create_node("Denominator")

        self._edge_token(denominator.digits, denominator_node)

        return denominator_node

    def visit_number(self, number: AST.Number) -> pydot.Node:
        """Perform visiting operation on Number node."""
        number_node = self._create_node("Number")

        self._edge_iterable(number.digits, number_node)

        return number_node

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> pydot.Node:
        """Perform visiting operation on timesig fraction node."""
        fraction_node = self._create_node("Fraction")

        self._edge_token(fraction.numerator, fraction_node)
        if fraction.denominator is not None:
            self._edge_token(fraction.denominator, fraction_node)

        return fraction_node
