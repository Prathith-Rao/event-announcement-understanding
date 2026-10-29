from scripts.collect import clean_paragraphs


def test_collect_only_natural_paragraph_not_synthesized_fields():
    paragraph = "We invite students to a workshop on responsible computing, with guided practical exercises and discussion."
    html = f'<html><header><p>Join another workshop in the navigation area, with a long description that is unrelated.</p></header><main><h1>SECRET TITLE</h1><table><tr><td>2099-01-01</td></tr></table><p>{paragraph}</p><p>Contact workshop@example.edu for information on a long and interesting training workshop.</p></main></html>'
    texts, _ = clean_paragraphs(html)
    assert texts == [paragraph]
    assert "SECRET TITLE" not in texts[0]
    assert "2099" not in texts[0]
