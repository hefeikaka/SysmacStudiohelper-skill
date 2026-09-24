# SysmacStudiohelper

面向欧姆龙 NJ/NX 和 Sysmac Studio 的自动化工程 skill，当前版本 v0.9.5。把工艺口语转成设备接口、功能 FB、程序段步序、ST、变量/组态资料及操作说明；先收到已有工程时，读取框架并优先按模板复用。

## 范围

只保留通用工作流、可复用踩坑规则、工具和条件明确的示例。项目的地址、协议契约、设备/程序数量、周期配置和交付状态留在项目目录。示例参数和回归用例不构成新工程的默认要求。

## 核心约定

- FB 封装设备/功能；跨设备步序放在程序段。
- 优先复用厂商轴/设备结构，FB内部读取已有成员，减少逐字段接线；先核对反馈、当前指令和最终目标的语义差异。
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
|scripts/check_wire_layout.py|检查固定二进制报文的类型宽度、数组维度、偏移、总长及传输容量|
|scripts/test_checks.py、scripts/test_initial.py|检查器及初版工具回归测试|
|assets/FB_Cylinder2Coil.iec|单设备功能 FB 模板|
|assets/PRG_Sequence.st|程序段中组织步序的示例|

Python 工具仅依赖标准库，工程索引需要 Python 3.11+。运行 `python scripts/test_checks.py` 和 `python scripts/test_initial.py`。检查参数与限制见 references/executable-checks.md、references/process-language.md。

通信模板扩展规则见 [protocol-projects.md](references/protocol-projects.md)。运行 `python scripts/check_wire_layout.py contract.json --capacity 2000` 可检查项目提供的字段契约；容量参数必须来自实际发布接口。`python scripts/test_wire_layout.py` 覆盖布局和容量错误。项目的实际数据格式不写死在skill中；命令中的容量仅为示例，必须替换为已确认的接口容量。

FB作用域与复合输出规则见 [fb-scope.md](references/fb-scope.md)。运行 `python scripts/check_fb_scope.py delivered.xml` 检查直接声明的FB类型；别名和保护库需要另外核对。

变量及ST的中文说明要求见 [chinese-documentation.md](references/chinese-documentation.md)。运行 `python scripts/check_chinese_comments.py delivered.xml` 检查中文注释覆盖；解释是否准确仍需人工审查。运行 `python -m unittest discover -s scripts -p "test_*.py"`，验证当前版本的检查器；具体结果记录在对应交付报告中。

运行 `python scripts/check_identifier_conflicts.py delivered.xml --namespace ExampleLibrary` 检查已知内置指令及库命名空间重名；命名空间按实际引用库提供，LIMIT是已知内置指令冲突案例。该检查不是完整的Sysmac名称解析器。

高速采样与慢速通信的拆分约定见 [multirate.md](references/multirate.md)：明确任务间交接对象、唯一写入者、原始时间、缓冲满处理、有界消费和启动/主动重载。程序数量按当前需求和任务边界确定；内部功能FB附说明，测试用TEST命名并独立交付。任务配置与原生性能需单独验证。

原平台无数据显示时，按 [data-chain-diagnosis.md](references/data-chain-diagnosis.md) 沿同一条报文追踪采样、Broker、解析模板、入库/推送和原页面。大量轴按动作抽样及并发评估见 [sampling-scheduling.md](references/sampling-scheduling.md)：以实际任务余量、队列水位及低频轴采样公平性确定容量。

可选：自行取得 Jiecc 7.x 后运行 `python scripts/test_templates.py --jiecc <jiecc路径>`，执行实际模板 ST。该脚本验证随附示例的行为；解释器测试不等于Sysmac原生编译。仓库不捆绑该第三方工具。

## 当前边界

已具备规则、默认补全、受限工程索引、检查器与源代码模板。尚无完整自由文本编译器、通用 smc 写回器、完整梯形图还原器或自动 Sysmac 编译/仿真执行器。模板未经目标 Sysmac 原生编译；静态检查通过不等于可投产。以后扩展 PackML 时复用设备FB，单独设计机器状态层。

仓库不包含用户实际工程、截图、第三方受保护源码、厂商手册或编译器。未声明开源许可证；如需开源授权，由维护者选择许可证。
