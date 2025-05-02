from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

from docutils import writers, nodes

try:
    import simplejson as json
except ImportError:
    import json

if TYPE_CHECKING:
    from typing import Optional, Tuple, Union

__docformat__ = "reStructuredText"


class ASTWriter(writers.Writer):
    supported = ("ast",)
    """Formats this writer supports."""

    config_section = "docutils_ast writer"
    config_section_dependencies = ("writers",)

    output = None
    """Final translated form of `document`."""

    def __init__(self):
        writers.Writer.__init__(self)
        self.translator_class = ASTTranslator
        self.visitor = None

    def translate(self):
        self.visitor = visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = "".join(visitor.output)


class ASTTranslator(nodes.GenericNodeVisitor):
    def __init__(self, document: nodes.document):
        nodes.NodeVisitor.__init__(self, document)
        result, _, _ = self.walk(document)
        self.output = [json.dumps(result)]

    def walk(
        self,
        node: nodes.Node,
        start: Optional[int] = 1,
        end: Optional[int] = None,
    ) -> Union[Tuple[dict, int, int], Tuple[None, None, None]]:
        if not isinstance(node, nodes.Node):
            return None, None, None
        result = {}
        # Attributes
        for k, v in node.__dict__.items():
            if k.startswith("__"):
                continue
            if not isinstance(v, (str, int, float, bool)):
                continue
            try:
                result[k] = v
            except NameError:
                pass
        # line
        if node.line:
            result["lineno"] = node.line
        # Tag Name (type)
        if "tagname" not in result:
            result["tagname"] = "text"
        # Text
        if isinstance(node, (nodes.Text,)):
            result["text"] = node.astext()

        # Line from node
        if isinstance(node, nodes.paragraph):
            if node.line:
                start = node.line
            if node.rawsource:
                end = start + len(node.rawsource.split("\n"))
        elif node.line:
            idx = node.parent.index(node)
            if idx == 0:
                start = 1
            else:
                start = end + 1
            end = node.line
        result["line"] = {
            "start": start,
        }

        # Children
        if node.children:
            children = []
            for child in node.children:
                result_, start, end = self.walk(child, start, end)
                children.append(result_)
            result["children"] = children

        # Line End
        result["line"]["end"] = end
        return result, start, end

    # GenericNodeVisitor methods
    def default_visit(self, node):
        """Default node visit method."""
        pass

    def default_departure(self, node):
        """Default node depart method."""
        pass

    # NodeVisitor methods
    def unknown_departure(self, node):
        pass

    def unknown_visit(self, node):
        pass
