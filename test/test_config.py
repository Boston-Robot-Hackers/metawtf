#!/usr/bin/env python3
"""Tests for metawtf.config.

Author: Pito Salas and Claude Code
Open Source Under MIT license
"""

import textwrap

import pytest

from metawtf.config import ConfigError, load_config, parse_config


def load(conf_text: str):
    return parse_config(textwrap.dedent(conf_text))


def test_minimal_valid_config_uses_default_sample_hz():
    config = load("echo /odom field=pose.pose.position.x name=odom_x\n")
    assert config.sample_hz == 5.0
    assert config.columns[0].name == "odom_x"
    assert config.columns[0].topic == "/odom"
    assert config.columns[0].field == "pose.pose.position.x"
    assert config.columns[0].type is None
    assert config.columns[0].stale_after is None


def test_explicit_sample_hz_and_optional_fields():
    config = load(
        """
        sample 10
        echo /odom field=pose.pose.position.x type=nav_msgs/msg/Odometry stale_after=2.0
        """
    )
    assert config.sample_hz == 10.0
    assert config.columns[0].type == "nav_msgs/msg/Odometry"
    assert config.columns[0].stale_after == 2.0


def test_default_name_is_sanitized_topic():
    config = load("echo /robot/odom field=pose.pose.position.x\n")
    assert config.columns[0].name == "robot_odom"


def test_missing_field_raises():
    with pytest.raises(ConfigError):
        load("echo /odom\n")


def test_non_numeric_sample_hz_raises():
    with pytest.raises(ConfigError):
        load("sample fast\necho /odom field=x\n")


def test_zero_sample_hz_raises():
    with pytest.raises(ConfigError):
        load("sample 0\necho /odom field=x\n")


def test_unknown_directive_raises():
    with pytest.raises(ConfigError, match="unknown directive"):
        load("bogus 1\necho /odom field=x\n")


def test_unknown_column_key_raises():
    with pytest.raises(ConfigError, match="unknown key"):
        load("echo /odom field=x bogus=1\n")


def test_invalid_stale_after_raises():
    with pytest.raises(ConfigError):
        load("echo /odom field=x stale_after=-1\n")


def test_no_column_directives_raises():
    with pytest.raises(ConfigError, match="no column"):
        load("sample 5\n")


def test_hz_single_topic_parses_with_default_window():
    config = load("hz /tf\n")
    column = config.columns[0]
    assert column.topic == "/tf"
    assert column.match is None
    assert column.name == "tf"
    assert column.window == 2.0


def test_hz_match_compiles_regex_and_has_no_name():
    config = load("hz match=^/tf window=3.0\n")
    column = config.columns[0]
    assert column.topic is None
    assert column.match.pattern == "^/tf"
    assert column.name is None
    assert column.window == 3.0


def test_hz_mixed_with_echo_columns():
    config = load(
        """
        echo /odom field=pose.pose.position.x
        hz /chatter
        """
    )
    assert config.columns[0].field == "pose.pose.position.x"
    assert config.columns[1].topic == "/chatter"


def test_hz_topic_and_match_together_raises():
    with pytest.raises(ConfigError):
        load("hz /tf match=^/tf\n")


def test_hz_neither_topic_nor_match_raises():
    with pytest.raises(ConfigError):
        load("hz\n")


def test_hz_bad_regex_raises():
    with pytest.raises(ConfigError, match="invalid regex"):
        load("hz match=[\n")


def test_hz_window_below_sample_period_raises():
    with pytest.raises(ConfigError, match="window"):
        load("sample 5.0\nhz /tf window=0.1\n")


def test_hz_window_checked_even_when_sample_comes_later():
    with pytest.raises(ConfigError, match="window"):
        load("hz /tf window=0.1\nsample 5.0\n")


def test_hz_name_with_match_raises():
    with pytest.raises(ConfigError, match="'name'"):
        load("hz match=^/tf name=foo\n")


def test_width_parses_on_echo_and_hz_columns():
    config = load(
        """
        echo /odom field=pose.pose.position.x width=10
        hz /tf width=6
        """
    )
    assert config.columns[0].width == 10
    assert config.columns[1].width == 6


def test_width_defaults_per_metric_when_omitted():
    config = load(
        """
        echo /odom field=x
        hz /tf
        proc_cpu name=cpu process=loop
        sys_cpu name=idle mode=idle
        """
    )
    assert config.columns[0].width == 8
    assert config.columns[1].width == 6
    assert config.columns[2].width == 6
    assert config.columns[3].width == 6


def test_non_integer_width_raises():
    with pytest.raises(ConfigError, match="integer"):
        load("echo /odom field=x width=3.5\n")


def test_zero_width_raises():
    with pytest.raises(ConfigError, match="> 0"):
        load("echo /odom field=x width=0\n")


def test_time_defaults_when_absent():
    config = load("echo /odom field=x\n")
    assert config.time.format is None
    assert config.time.width is None


def test_time_format_and_width_parse():
    config = load("time format=%H:%M:%S width=12\necho /odom field=x\n")
    assert config.time.format == "%H:%M:%S"
    assert config.time.width == 12


def test_time_unknown_key_raises():
    with pytest.raises(ConfigError, match="unknown key"):
        load("time bogus=1\necho /odom field=x\n")


def test_time_positional_raises():
    with pytest.raises(ConfigError, match="positional"):
        load("time 3\necho /odom field=x\n")


def test_plain_echo_has_json_false_and_no_subfields():
    config = load("echo /odom field=x\n")
    assert config.columns[0].is_json is False
    assert config.columns[0].subfields is None


def test_json_subfields_parse():
    config = load(
        "echo /explore/status field=data json=true subfields=reached,failed\n"
    )
    column = config.columns[0]
    assert column.is_json is True
    assert column.subfields == ["reached", "failed"]
    assert column.name == "explore_status"


def test_subfields_without_json_raises():
    with pytest.raises(ConfigError, match="json"):
        load("echo /s field=data subfields=a\n")


def test_name_with_multiple_subfields_raises():
    with pytest.raises(ConfigError, match="'name'"):
        load("echo /s field=data json=true subfields=a,b name=foo\n")


def test_name_with_single_subfield_is_column_header():
    config = load("echo /s field=data json=true subfields=reached name=foo\n")
    assert config.columns[0].subfield_names == ["foo"]


def test_subfield_names_derive_from_topic_and_keys():
    config = load(
        "echo /explore/status field=data json=true"
        " subfields=reached,payload.count\n"
    )
    assert config.columns[0].subfield_names == [
        "explore_status_reached",
        "explore_status_payload_count",
    ]


def test_subfield_widths_parse_one_per_subfield():
    config = load(
        "echo /s field=data json=true subfields=a,b,c width=4,10,6\n"
    )
    assert config.columns[0].subfield_widths == [4, 10, 6]


def test_subfield_widths_default_when_width_omitted():
    config = load("echo /s field=data json=true subfields=a,b\n")
    assert config.columns[0].subfield_widths == [8, 8]


def test_subfield_width_count_mismatch_raises():
    with pytest.raises(ConfigError, match="comma-separated"):
        load("echo /s field=data json=true subfields=a,b,c width=4,10\n")


def test_non_integer_subfield_width_raises():
    with pytest.raises(ConfigError, match="integer"):
        load("echo /s field=data json=true subfields=a,b width=4,x\n")


def test_multi_field_parses_into_columns():
    config = load("echo /cmd_vel field=linear.x,angular.z\n")
    column = config.columns[0]
    assert column.fields == ["linear.x", "angular.z"]
    assert column.field is None
    assert column.field_names == ["cmd_vel_linear_x", "cmd_vel_angular_z"]
    assert column.field_widths == [8, 8]


def test_single_field_stays_single_column():
    config = load("echo /cmd_vel field=linear.x name=vx\n")
    column = config.columns[0]
    assert column.field == "linear.x"
    assert column.fields is None
    assert column.name == "vx"


def test_multi_field_per_field_widths():
    config = load("echo /cmd_vel field=linear.x,angular.z width=4,10\n")
    assert config.columns[0].field_widths == [4, 10]


def test_missing_field_raises_with_field_message():
    with pytest.raises(ConfigError, match="field"):
        load("echo /cmd_vel\n")


def test_multi_field_with_json_raises():
    with pytest.raises(ConfigError, match="single 'field'"):
        load("echo /s field=a,b json=true\n")


def test_multi_field_name_count_mismatch_raises():
    with pytest.raises(ConfigError, match="'name'"):
        load("echo /cmd_vel field=linear.x,angular.z name=foo\n")


def test_multi_field_width_count_mismatch_raises():
    with pytest.raises(ConfigError, match="comma-separated"):
        load("echo /cmd_vel field=linear.x,angular.z width=4\n")


def test_multi_field_custom_names():
    config = load("echo /cmd_vel field=linear.x,angular.z name=vx,wz\n")
    assert config.columns[0].field_names == ["vx", "wz"]


def test_subfields_custom_names():
    config = load(
        "echo /s field=data json=true subfields=a,b name=aa,bb\n"
    )
    assert config.columns[0].subfield_names == ["aa", "bb"]


def test_empty_subfields_value_raises():
    with pytest.raises(ConfigError):
        load("echo /s field=data json=true subfields=\n")


def test_non_bool_json_raises():
    with pytest.raises(ConfigError, match="true or false"):
        load("echo /s field=data json=yes_please\n")


def test_proc_cpu_parses_with_compiled_regex():
    config = load("proc_cpu name=cpu_loop process=busyloop\n")
    column = config.columns[0]
    assert column.name == "cpu_loop"
    assert column.process.pattern == "busyloop"
    assert column.width == 6


def test_proc_cpu_width_parses():
    config = load("proc_cpu name=c process=x width=8\n")
    assert config.columns[0].width == 8


def test_proc_cpu_missing_name_raises():
    with pytest.raises(ConfigError, match="'name'"):
        load("proc_cpu process=x\n")


def test_proc_cpu_missing_process_raises():
    with pytest.raises(ConfigError, match="'process'"):
        load("proc_cpu name=c\n")


def test_proc_cpu_bad_regex_raises():
    with pytest.raises(ConfigError, match="invalid regex"):
        load("proc_cpu name=c process=[\n")


def test_proc_cpu_unknown_key_raises():
    with pytest.raises(ConfigError, match="unknown key"):
        load("proc_cpu name=c process=x topic=/t\n")


def test_proc_cpu_positional_raises():
    with pytest.raises(ConfigError, match="positional"):
        load("proc_cpu /x name=c process=x\n")


def test_sys_cpu_parses_with_default_width():
    config = load("sys_cpu name=cpu_idle mode=idle\n")
    column = config.columns[0]
    assert column.name == "cpu_idle"
    assert column.mode == "idle"
    assert column.width == 6


def test_sys_cpu_width_parses():
    config = load("sys_cpu name=c mode=busy width=9\n")
    assert config.columns[0].width == 9


def test_sys_cpu_missing_name_raises():
    with pytest.raises(ConfigError, match="'name'"):
        load("sys_cpu mode=busy\n")


def test_sys_cpu_missing_mode_raises():
    with pytest.raises(ConfigError, match="'mode'"):
        load("sys_cpu name=c\n")


def test_sys_cpu_bad_mode_raises():
    with pytest.raises(ConfigError, match="'mode'"):
        load("sys_cpu name=c mode=user\n")


def test_sys_cpu_unknown_key_raises():
    with pytest.raises(ConfigError, match="unknown key"):
        load("sys_cpu name=c mode=busy process=x\n")


def test_comments_and_blank_lines_are_skipped():
    config = load(
        """
        # a comment

        sample 2
          # an indented comment
        echo /odom field=x
        """
    )
    assert config.sample_hz == 2.0
    assert len(config.columns) == 1


def test_repeated_key_raises():
    with pytest.raises(ConfigError, match="repeated key"):
        load("echo /odom field=x field=y\n")


def test_two_positionals_raise():
    with pytest.raises(ConfigError, match="positional"):
        load("echo /odom /other field=x\n")


def test_topic_given_positionally_and_as_key_raises():
    with pytest.raises(ConfigError, match="topic given twice"):
        load("echo /odom topic=/other field=x\n")


def test_malformed_token_raises():
    with pytest.raises(ConfigError, match="malformed token"):
        load("echo /odom field=\n")


def test_repeated_sample_directive_raises():
    with pytest.raises(ConfigError, match="repeated 'sample'"):
        load("sample 2\nsample 3\necho /odom field=x\n")


def test_repeated_time_directive_raises():
    with pytest.raises(ConfigError, match="repeated 'time'"):
        load("time width=7\ntime width=8\necho /odom field=x\n")


def test_format_defaults_to_none_for_auto_detect():
    config = load("echo /odom field=x\n")
    assert config.output_format is None


def test_format_human_and_csv_parse():
    assert load("format human\necho /odom field=x\n").output_format == "human"
    assert load("format csv\necho /odom field=x\n").output_format == "csv"


def test_format_bad_value_raises():
    with pytest.raises(ConfigError, match="'format'"):
        load("format json\necho /odom field=x\n")


def test_format_missing_value_raises():
    with pytest.raises(ConfigError, match="'format'"):
        load("format\necho /odom field=x\n")


def test_auto_header_for_indexed_path():
    config = load("echo /oak/detections field=detections[0].id,header.seq\n")
    assert config.columns[0].field_names == [
        "oak_detections_detections_0_id",
        "oak_detections_header_seq",
    ]


def test_auto_header_for_length_path():
    config = load("echo /oak/detections field=detections.#,header.seq\n")
    assert config.columns[0].field_names == [
        "oak_detections_detections_n",
        "oak_detections_header_seq",
    ]


def test_auto_header_for_negative_index_path():
    config = load("echo /oak/detections field=detections[-1].id,header.seq\n")
    assert config.columns[0].field_names[0] == "oak_detections_detections_n1_id"


def test_explicit_name_wins_over_indexed_auto_header():
    config = load(
        "echo /oak/detections field=detections.#,detections[0].id name=ntrk,first\n"
    )
    assert config.columns[0].field_names == ["ntrk", "first"]


def test_format_with_options_raises():
    with pytest.raises(ConfigError, match="no key=value"):
        load("format human width=3\necho /odom field=x\n")


def test_repeated_format_directive_raises():
    with pytest.raises(ConfigError, match="repeated 'format'"):
        load("format human\nformat csv\necho /odom field=x\n")


def test_sample_with_options_raises():
    with pytest.raises(ConfigError, match="no key=value"):
        load("sample 2 width=3\necho /odom field=x\n")


def test_error_names_the_line_number():
    with pytest.raises(ConfigError, match="line 2"):
        load("echo /odom field=x\nhz\n")


def test_load_config_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="cannot read config"):
        load_config(tmp_path / "nope.conf")


def test_load_config_reads_conf_file(tmp_path):
    conf = tmp_path / "metawtf.conf"
    conf.write_text("sample 2\necho /odom field=x\n")
    config = load_config(conf)
    assert config.sample_hz == 2.0
    assert config.columns[0].topic == "/odom"
