import pytest

from locify.tree_sitter.parser import TagKind, TreeSitterParser


@pytest.fixture
def parser(tmp_path):
    return TreeSitterParser(cache_root_dir=str(tmp_path))


def test_get_tags_from_python_file(parser, tmp_path):
    # Create a temporary Python file
    python_file = tmp_path / 'test.py'

    python_content = """
def hello_world():
    print("Hello, World!")

def main():
    hello_world()

if __name__ == "__main__":
    main()
"""
    python_file.write_text(python_content)

    # Get tags from the file
    tags = parser.get_tags_from_file(
        str(python_file.absolute()), str(python_file.relative_to(tmp_path))
    )

    # Verify we got some tags
    assert len(tags) > 0
    # Check that we found the function definitions
    def_tags = [tag for tag in tags if tag.tag_kind == TagKind.DEF]
    print(def_tags)
    assert any(tag.node_name == 'hello_world' for tag in def_tags)
    assert any(tag.node_name == 'main' for tag in def_tags)


def test_get_tags_from_nonexistent_file(parser):
    tags = parser.get_tags_from_file('/path/that/does/not/exist/file.py', 'file.py')
    assert tags == []


def test_get_tags_from_unsupported_file(parser, tmp_path):
    # Test with a file type that doesn't have a tree-sitter grammar
    unsupported_file = tmp_path / 'test.xyz'
    unsupported_file.write_text('Some content')

    tags = parser.get_tags_from_file(
        str(unsupported_file.absolute()), str(unsupported_file.relative_to(tmp_path))
    )
    assert tags == []


def test_get_tags_from_java_file(parser, tmp_path):
    # Create a temporary Java file
    java_file = tmp_path / 'Test.java'
    java_content = """
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }

    public void greet() {
        main(null);
    }
}
"""
    java_file.write_text(java_content)

    tags = parser.get_tags_from_file(
        str(java_file.absolute()), str(java_file.relative_to(tmp_path))
    )

    # Verify we got some tags
    assert len(tags) > 0
    # Check that we found the class and method definitions
    def_tags = [tag for tag in tags if tag.tag_kind == TagKind.DEF]
    assert any(tag.node_name == 'Test' for tag in def_tags)
    assert any(tag.node_name == 'main' for tag in def_tags)
    assert any(tag.node_name == 'greet' for tag in def_tags)


def test_get_tags_from_empty_file(parser, tmp_path):
    # Test with an empty file
    empty_file = tmp_path / 'empty.py'
    empty_file.write_text('')

    tags = parser.get_tags_from_file(
        str(empty_file.absolute()), str(empty_file.relative_to(tmp_path))
    )
    assert tags == []
