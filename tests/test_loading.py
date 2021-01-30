"""Tests for loading from a file."""

# pylint: disable=unused-variable

from dataclasses import dataclass

import pytest

from datafiles import datafile
from datafiles.utils import dedent, logbreak, read, write

from .samples import (
    Sample,
    SampleAsJSON,
    SampleWithDefaults,
    SampleWithList,
    SampleWithListAndDefaults,
    SampleWithListOfDataclasses,
    SampleWithNesting,
    _NestedSample1,
)


def describe_nominal():
    @pytest.fixture
    def sample():
        return Sample(None, None, None, None)

    def with_matching_types(sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: true
            int_: 1
            float_: 2.3
            str_: 'foobar'
            """,
        )

        sample.datafile.load()

        expect(sample.bool_).is_(True)
        expect(sample.int_) == 1
        expect(sample.float_) == 2.3
        expect(sample.str_) == 'foobar'

    def with_convertable_types(sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: 1
            int_: 2
            float_: 3
            str_: 4
            """,
        )

        sample.datafile.load()

        expect(sample.bool_).is_(True)
        expect(sample.int_) == 2
        expect(sample.float_) == 3.0
        expect(sample.str_) == '4'

    def with_extra_fields(sample, expect):
        write(
            'tmp/sample.yml',
            """
            bool_: null
            int_: null
            float_: null
            str_: null

            extra: 5
            """,
        )

        sample.datafile.load()

        expect(hasattr(sample, 'extra')).is_(False)

    def with_invalid_data(sample, expect):
        write(
            'tmp/sample.yml',
            """
            - foo
            - bar
            """,
        )

        sample.datafile.load()

        expect(sample.int_) == 0


def describe_alternate_formats():
    @pytest.fixture
    def sample():
        return SampleAsJSON(None, None, None, None)

    def with_json(sample, expect):
        write(
            'tmp/sample.json',
            """
            {
                "bool_": true,
                "int_": 1,
                "float_": 2.3,
                "str_": "foobar"
            }
            """,
        )

        sample.datafile.load()

        expect(sample.bool_).is_(True)
        expect(sample.int_) == 1
        expect(sample.float_) == 2.3
        expect(sample.str_) == 'foobar'


def describe_default_values():
    @pytest.fixture
    def sample():
        return SampleWithDefaults(None)

    def with_empty_file(sample, expect):
        write('tmp/sample.yml', "")

        sample.datafile.load()

        expect(sample.with_default) == 'foo'
        expect(sample.without_default) == ''

    def with_partial_file(sample, expect):
        write(
            'tmp/sample.yml',
            """
            without_default: bar
            """,
        )

        sample.datafile.load()

        expect(sample.with_default) == 'foo'
        expect(sample.without_default) == 'bar'


def describe_nesting():
    @pytest.fixture
    def sample():
        return SampleWithNesting(None, None, None)

    def with_defaults(sample, expect):
        write(
            'tmp/sample.yml',
            """
            name: ''
            score: 0.0
            nested:
              name: ''
              score: 0.0
            """,
        )

        sample.datafile.load()

        expect(sample.name) == ''
        expect(sample.score) == 0.0
        expect(sample.nested.name) == ''
        expect(sample.nested.score) == 0.0

    def with_convertable_types(sample, expect):
        write(
            'tmp/sample.yml',
            """
            name: 1
            score: '2.3'
            nested:
              name: 4
              score: '5.6'
            """,
        )

        sample.datafile.load()

        expect(sample.name) == '1'
        expect(sample.score) == 2.3
        expect(sample.nested.name) == '4'
        expect(sample.nested.score) == 5.6

    def with_missing_keys(sample, expect):
        write(
            'tmp/sample.yml',
            """
            name: foo
            nested:
              name: bar
            """,
        )

        sample.datafile.load()

        expect(sample.name) == 'foo'
        expect(sample.score) == 0.0
        expect(sample.nested.name) == 'bar'
        expect(sample.nested.score) == 0.0

    def with_missing_nested_object(sample, expect):
        sample.nested = _NestedSample1(name='bar', score=8)

        write(
            'tmp/sample.yml',
            """
            name: foo
            score: 7
            """,
        )

        sample.datafile.load()

        expect(sample.name) == 'foo'
        expect(sample.score) == 7.0
        expect(sample.nested.name) == 'bar'
        expect(sample.nested.score) == 8.0

    def with_extra_attributes(sample, expect):
        write(
            'tmp/sample.yml',
            """
            name: 'a'
            score: 1.2
            nested:
              name: 'b'
              score: 3.4
              extra: 5
            """,
        )

        sample.datafile.load()

        expect(sample.name) == 'a'
        expect(sample.score) == 1.2
        expect(sample.nested.name) == 'b'
        expect(sample.nested.score) == 3.4
        expect(hasattr(sample.nested, 'extra')).is_(False)

    def with_multiple_levels(expect):
        @dataclass
        class Bottom:
            level: int = 4

        @dataclass
        class C:
            level: int = 3
            d: Bottom = Bottom()

        @dataclass
        class B:
            level: int = 2
            c: C = C()

        @dataclass
        class A:
            level: int = 1
            b: B = B()

        @datafile('../tmp/sample.toml', defaults=True, auto_save=False)
        class Top:
            level: int = 0
            a: A = A()

        sample = Top()

        expect(read('tmp/sample.toml')) == dedent(
            """
            level = 0

            [a]
            level = 1

            [a.b]
            level = 2

            [a.b.c]
            level = 3

            [a.b.c.d]
            level = 4
            """
        )

        logbreak("Modifying attribute")
        sample.a.b.c.d.level = 99

        expect(read('tmp/sample.toml')) == dedent(
            """
            level = 0

            [a]
            level = 1

            [a.b]
            level = 2

            [a.b.c]
            level = 3

            [a.b.c.d]
            level = 99
            """
        )

        write(
            'tmp/sample.toml',
            """
            level = 0

            [a]
            level = 10

            [a.b]
            level = 20

            [a.b.c]
            level = 30

            [a.b.c.d]
            level = 40
            """,
        )

        logbreak("Reading attribute")
        expect(sample.a.level) == 10
        expect(sample.a.b.level) == 20
        expect(sample.a.b.c.level) == 30

        expect(sample.a.b.c.d.level) == 40


def describe_lists():
    def with_matching_types(expect):
        write(
            'tmp/sample.yml',
            """
            items:
            - 1.2
            - 3.4
            """,
        )

        sample = SampleWithList(None)

        expect(sample.items) == [1.2, 3.4]

    def with_conversion(expect):
        write(
            'tmp/sample.yml',
            """
            items: 1, 2.3
            """,
        )

        sample = SampleWithList(None)

        expect(sample.items) == [1.0, 2.3]

    def with_conversion_and_defaults(expect):
        write(
            'tmp/sample.yml',
            """
            items: 1, 2.3
            """,
        )

        sample = SampleWithListAndDefaults()

        expect(sample.items) == [1.0, 2.3]

    def with_null_list_value(expect):
        write(
            'tmp/sample.yml',
            """
            items:
            -
            """,
        )

        sample = SampleWithListOfDataclasses()

        expect(sample.items) == []

    def with_partial_list_value(expect):
        write(
            'tmp/sample.yml',
            """
            items:
            - name: abc
            """,
        )

        logbreak()
        sample = SampleWithListOfDataclasses()
        logbreak()

        expect(sample.items) == [_NestedSample1(name='abc', score=0.0)]
