# FB 实例作用域与复合输出

依据：Omron W501《NJ/NX-series CPU Unit Software User's Manual》§6-3-10（FB实例是所属程序的局部变量，不能作为全局变量）、§6-2-5（允许实例数组、允许变量下标、不能从其他POU读取FB实例）。按目标版本核对手册。曾在实际 Sysmac 导入后的编译中遇到全局 FB 数组及复合输出元素访问错误；XSD和第三方ST解释器均未发现这些厂商语义限制。

- 功能FB仍然封装采集、统计、编码等功能。所属程序的局部变量可声明实例或实例数组；不要为了规避全局限制而无条件展开成大量独立实例。
- 程序间共享普通 STRUCT/ARRAY 数据，不能把 FB 实例当作共享数据容器。列出共享数据的唯一写入者及消费者、任务调用顺序。
- FB输出为结构体或数组时，先用命名输出关联 `Data => SharedData` 或整体复制 `SharedData := Instance.Data`，随后访问 `SharedData.Member` / `SharedData[i]`。避免直接使用 `Instance.Data.Member`、`Instance.Payload[i]`。标量输出 `Instance.Done` 可直接读取。
- 将全局实例替换成普通数据时，同步更新所有引用POU的外部变量类型、属性、命名空间；不能只改全局变量表。
- FB输出带初值时，共享结构的默认零值不等于原FB输出初值。检查首扫描的 Ready/CanStart、复位、待发送快照和跨扫描状态，防止迁移后漏掉首个触发。
- 修复已有导入工程时，优先导出最小补丁；保留用户I/O绑定、原模板通信程序、运行参数和保持变量。补丁依赖旧版已有类型时，应明确“只能用于已经导入旧版的工程”。

检查命令：`python scripts/check_fb_scope.py delivered.xml`。

检查器识别XML中直接声明的FB类型，包括实例数组，拒绝全局FB变量以及对已声明FB输出的继续成员/数组访问。它不解析类型别名、嵌套命名空间、保护库接口或完整ST语义；无报错只表示这些检查通过，不能称为Sysmac编译通过。单独的补丁XML可能不包含FB定义，应对完整包运行检查，再检查补丁范围和官方XSD。

回归：`python -m unittest discover -s scripts -p "test_*.py"`。保留已失败版本或测试夹具，证明检查器能拒绝旧模式，同时允许局部FB数组和普通共享结构。
