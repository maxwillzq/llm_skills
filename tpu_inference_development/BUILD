load("//learning/gemini/agents/skill_rules:skills.bzl", "agent_skill")
load("//learning/gemini/agents/skills/skill_creator/scripts:skill_defs.bzl", "validate_skill_test")
load("//third_party/bazel_rules/rules_shell/shell:sh_binary.bzl", "sh_binary")

package(default_visibility = ["//visibility:public"])

validate_skill_test(
    name = "validate_vllm_on_tpu_skill_test",
)

agent_skill(
    name = "vllm-on-tpu",
    srcs = [
        "SKILL.md",
        "scripts/tpu_dev_sync.sh",
    ],
)

sh_binary(
    name = "tpu_dev_sync_tool",
    srcs = ["scripts/tpu_dev_sync.sh"],
)
