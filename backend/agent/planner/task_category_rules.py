from __future__ import annotations


class TaskCategoryRules:
    """
    Task classification rule registry.

    Responsibility:
        - provide category rules
        - provide classifier matching data

    Not Responsible:
        - classification
        - analysis
        - planning
        - execution
    """

    VERSION = "4.1"

    CATEGORY_RULES = {
        "workspace_scan": (
            "项目结构",
            "目录结构",
            "文件结构",
            "文件树",
            "扫描项目",
            "扫描目录",
            "扫描",
            "遍历",
            "统计",
            "tree",
            "workspace",
            "repository",
            "codebase",
        ),
        "code_analysis": (
            "搜索代码",
            "查找代码",
            "代码在哪里",
            "分析代码",
            "源码分析",
            "查看代码",
            "理解代码",
            "代码结构",
            "结构分析",
            "模块结构",
            "依赖",
            "质量",
            "grep",
            "search",
            "find",
            "analyze",
        ),
        "file_edit": (
            "修改",
            "编辑",
            "替换",
            "重构",
            "修复",
            "添加",
            "新增",
            "增加",
            "插入",
            "追加",
            "删除",
            "移除",
            "重命名",
            "更新",
            "改成",
            "改为",
            "edit",
            "modify",
            "add",
            "insert",
            "append",
            "remove",
            "delete",
            "rename",
            "update",
            "replace",
            "refactor",
            "fix",
        ),
        "file_read": (
            "读取",
            "打开",
            "查看",
            "read",
            "open",
            "cat",
        ),
        "file_write": (
            "创建文件",
            "新建文件",
            "生成文件",
            "写入文件",
            "保存文件",
            "create file",
            "write file",
            "save file",
        ),
        "test": (
            "测试",
            "pytest",
            "unit test",
            "验证",
        ),
        "deployment": (
            "部署",
            "服务器",
            "环境",
            "上线",
            "发布",
            "deployment",
            "deploy",
            "server",
        ),
        "summary": (
            "总结",
            "概括",
            "摘要",
            "汇总",
            "总结一下",
            "summarize",
            "summary",
        ),
        "text_generate": (
            "生成一段文本",
            "生成文本",
            "写一段文字",
            "写一段文本",
            "写文本",
            "生成回复",
            "写回复",
            "generate text",
            "generate a paragraph",
            "write text",
        ),
        "research": (
            "查询",
            "资料",
            "研究",
            "解释",
            "research",
            "query",
        ),
    }

    WORKSPACE_TARGETS = (
        "目录",
        "项目",
        "project",
        "workspace",
        "文件树",
        "repository",
        "codebase",
    )

    WORKSPACE_ACTIONS = (
        "扫描",
        "遍历",
        "统计",
        "查找",
        "超过",
        "分析",
        "理解",
        "结构",
        "architecture",
        "analyze",
        "understand",
        "inspect",
    )

    CODE_TARGETS = (
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".json",
        ".yaml",
        ".yml",
        "代码",
        "模块",
        "函数",
        "class",
        "backend",
        "src",
    )

    CODE_ACTIONS = (
        "分析",
        "理解",
        "结构",
        "依赖",
        "质量",
        "analyze",
        "understand",
        "inspect",
    )

    FILE_EXTENSIONS = (
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".json",
        ".yaml",
        ".yml",
        ".txt",
        ".md",
    )


__all__ = [
    "TaskCategoryRules",
]
