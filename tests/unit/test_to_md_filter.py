# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit test module for to_md_filter().
"""

import re
import pytest

from ansible_doc_template_extractor.cli import to_md_filter


TESTCASES_TO_MD_FILTER = [
    # Testcases for test_to_md_filter().

    # Each item is a tuple with these items:
    # - desc: Testcase description.
    # - input_text (str): Input text argument.
    # - exp_result (str): Expected result, or None for failure.
    # - exp_exc_type (type): Expected exception type for failure, or None for
    #   success.
    # - exp_exc_pattern (str): Expected regex pattern for exception message for
    #   failure, or None for success.

    (
        "Empty string",
        "",
        "",
        None,
        None
    ),
    (
        "Just NL",
        "\n",
        " ",
        None,
        None
    ),
    (
        "One line without trailing dot or NL",
        "The quick brown fox",
        "The quick brown fox",
        None,
        None
    ),
    (
        "One line with trailing dot",
        "The quick brown fox.",
        "The quick brown fox\\.",
        None,
        None
    ),
    (
        "One line with trailing NL",
        "The quick brown fox\n",
        "The quick brown fox",
        None,
        None
    ),
    (
        "One line with multiple trailing NL",
        "The quick brown fox\n\n\n",
        "The quick brown fox",
        None,
        None
    ),
    (
        "Two lines without trailing NL",
        "The quick brown fox\nJumps over the lazy dog",
        "The quick brown fox\nJumps over the lazy dog",
        None,
        None
    ),
    (
        "Two lines with trailing NL",
        "The quick brown fox\nJumps over the lazy dog\n",
        "The quick brown fox\nJumps over the lazy dog",
        None,
        None
    ),
    (
        "Multiple blanks are preserved",
        "Text with    4 blanks",
        "Text with    4 blanks",
        None,
        None
    ),
    (
        "Multiple NL are normalized to one",
        "First line\n\n\nFourth line",
        "First line\nFourth line",
        None,
        None
    ),
    (
        "Printable Unicode chars in BMP range are preserved",
        "\u00e9\u1e01",
        "\u00e9\u1e01",
        None,
        None
    ),
    (
        "Printable Unicode chars in SMP range are preserved",
        "\U00010141\U0001d11e",
        "\U00010141\U0001d11e",
        None,
        None
    ),
    (
        "Underscore is escaped",
        "my_var",
        "my\\_var",
        None,
        None
    ),
    (
        "Comma is preserved",
        "value, and",
        "value\\, and",
        None,
        None
    ),
    (
        "Asterisk list chars are preserved",
        "* List item 1",
        "* List item 1",
        None,
        None
    ),
    (
        "Dash list chars are preserved",
        "- List item 1",
        "- List item 1",
        None,
        None
    ),
    (
        "Number list chars are preserved",
        "# List item 1",
        "# List item 1",
        None,
        None
    ),
    (
        "Ansible markup C() is processed",
        "The C(quick) brown fox",
        "The <code>quick</code> brown fox",
        None,
        None
    ),
    (
        "Comma after Ansible markup C() is escaped",
        "The C(quick), brown fox",
        "The <code>quick</code>\\, brown fox",
        None,
        None
    ),
    (
        "Ansible markup B() is processed",
        "The B(quick) brown fox",
        "The <b>quick</b> brown fox",
        None,
        None
    ),
    (
        "Ansible markup I() is processed",
        "The I(quick) brown fox",
        "The <em>quick</em> brown fox",
        None,
        None
    ),
    (
        "Ansible markup HORIZONTALLINE is processed",
        "The quick brown fox HORIZONTALLINE jumps over the lazy dog",
        "The quick brown fox<hr>jumps over the lazy dog",
        None,
        None
    ),
    (
        "Ansible markup O() is processed",
        "For O(state=present) the",
        "For <code>state\\=present</code> the",
        None,
        None
    ),
    (
        "Ansible markup V() is processed",
        "Value V(blue) is",
        "Value <code>blue</code> is",
        None,
        None
    ),
    (
        "Ansible markup RV() is processed",
        "Return value RV(color=blue) is",
        "Return value <code>color\\=blue</code> is",
        None,
        None
    ),
    (
        "Ansible markup E() is processed",
        "Env var E(MYVAR) is",
        "Env var <code>MYVAR</code> is",
        None,
        None
    ),
    (
        "Ansible markup R() is processed",
        "See R(Heading 1,heading1) for",
        "See Heading 1 for",
        None,
        None
    ),
    (
        "Ansible markup L() is processed",
        "See L(Ansible,https://www.ansible.com) for",
        "See [Ansible](https\\://www\\.ansible\\.com) for",
        None,
        None
    ),
    (
        "Ansible markup U() is processed",
        "See U(https://www.ansible.com) for",
        "See [https\\://www\\.ansible\\.com](https\\://www\\.ansible\\.com) "
        "for",
        None,
        None
    ),
    (
        "Ansible markup M() for ansible.builtin is processed",
        "See M(ansible.builtin.yum) for",
        "See ansible\\.builtin\\.yum for",
        None,
        None
    ),
    (
        "Ansible markup M() for my.collection is processed",
        "See M(my.collection.foo) for",
        "See my\\.collection\\.foo for",
        None,
        None
    ),
    (
        "Ansible markup P() for ansible.builtin is processed",
        "See P(ansible.builtin.file#lookup) for",
        "See ansible\\.builtin\\.file for",
        None,
        None
    ),
    (
        "Ansible markup P() for my.collection is processed",
        "See P(my.collection.zick#zack) for",
        "See my\\.collection\\.zick for",
        None,
        None
    ),
    (
        ":ref: construct is escaped",
        "See section :ref:`heading1` is",
        "See section \\:ref\\:\\`heading1\\` is",
        None,
        None
    ),
]


@pytest.mark.parametrize(
    "desc, input_text, exp_result, exp_exc_type, exp_exc_pattern",
    TESTCASES_TO_MD_FILTER)
def test_to_md_filter(
        desc, input_text, exp_result, exp_exc_type, exp_exc_pattern):
    # pylint: disable=unused-argument
    """
    Test function for to_md_filter() function.
    """

    if exp_exc_type:
        with pytest.raises(exp_exc_type) as exc_info:

            # The code to be tested
            to_md_filter(input_text)

        exc = exc_info.value
        exc_msg = str(exc)
        if exp_exc_pattern:
            assert re.search(exp_exc_pattern, exc_msg, re.M)
    else:

        # The code to be tested
        result = to_md_filter(input_text)
        assert result == exp_result
