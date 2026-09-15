# SysmacStudiohelper

面向欧姆龙 NJ/NX 和 Sysmac Studio 的自动化工程 skill 初版。把工艺口语转成设备接口、功能 FB、程序段步序、ST、变量/组态资料及操作说明；先收到已有工程时，读取框架并优先按模板复用。

## 核心约定

- “气缸推出”：默认 Home/Work 两到位检测、两路控制、双线圈互锁；已有工程和明确要求优先。
- “皮带到位后气缸推出”：默认到位信号 TRUE 时同一扫描停皮带并请求推出，不默认等待传感器消失或插入延时。
- FB 封装设备/功能；跨设备步序放在程序段。
- 交付包含导入步骤、变量、I/O、项目树、任务/程序段顺序、FB 职责和验证范围。
- smc/smc2 先检查真实格式与框架；现有 FB/ST 能复用就复用。梯形图内嵌 ST 保留原归属及导通条件。

## 使用

将本仓库内容放入 Codex 的 skills/sysmacstudiohelper 目录，入口为 SKILL.md。显示项目名为 SysmacStudiohelper，skill 标识为 `sysmacstudiohelper`。

示例请求：“先读取这份工程作为模板，等我提供新工艺。”“根据这段工艺生成设备功能FB、程序段步序及完整导入说明。”

## 代码

|资源|功能|
|---|---|
|scripts/expand_devices.py|补全已经由模型识别的设备接口，不冒充自然语言解析器|
|scripts/inspect_project.py|只读索引 ZIP 型工程的 Entity 和代码标记，不破解保护|
|scripts/check_exports.py|检查 AML 顺序、轴速度换算、外部轴声明及常量属性|
|scripts/test_checks.py、scripts/test_initial.py|检查器及初版工具回归测试|
|assets/FB_Cylinder2Coil.iec|单设备功能 FB 模板|
|assets/PRG_Sequence.st|程序段中组织步序的示例|

Python 工具仅依赖标准库，工程索引需要 Python 3.11+。运行 `python scripts/test_checks.py` 和 `python scripts/test_initial.py`。检查参数与限制见 references/executable-checks.md、references/process-language.md。

可选：自行取得 Jiecc 7.x 后运行 `python scripts/test_templates.py --jiecc <jiecc路径>`，执行实际模板 ST。当前 16 项 Python 测试和 13 项 ST 解释器检查通过，包含同一扫描停输送/请求推出；这不是 Sysmac 原生编译记录。仓库不捆绑该第三方工具。

## 当前边界

已具备规则、默认补全、受限工程索引、检查器与源代码模板。尚无完整自由文本编译器、通用 smc 写回器、完整梯形图还原器或自动 Sysmac 编译/仿真执行器。模板未经目标 Sysmac 原生编译；静态检查通过不等于可投产。以后扩展 PackML 时复用设备FB，单独设计机器状态层。

仓库不包含用户实际工程、截图、第三方受保护源码、厂商手册或编译器。未声明开源许可证；如需开源授权，由维护者选择许可证。
