# 可执行检查与已发生的失败

脚本需要 Python 3 标准库，无第三方依赖。全部只读源 XML；只有显式指定 --report 时写结果文件。返回码 0 表示该项检查未发现错误，1 表示失败。结果中的 warnings 仍需处理，不得把范围有限的通过说成整个项目通过。

## 使用方式

在 skill 目录运行以下命令，实际路径作为参数传入，不改脚本常量：

```text
python scripts/check_exports.py aml <硬件文件.aml>
python scripts/check_exports.py axis <轴设置.xml> --pulse-velocity-limit <目标允许的脉冲每秒上限>
python scripts/check_exports.py bindings <程序.xml> --contract <已核对的轴引用.json>
python scripts/test_checks.py
```

支持范围：无命名空间的 CAEX 2.15 InternalElement 排列、重复 ID 和连接端点；Sysmac 轴 XML 的无减速器单位换算及速度范围；IEC61131-10 Program 的明确外部轴声明及类型/constant 匹配。其他 CAEX 版本、减速器比例、结构类型声明、ST 全量符号解析需另行核对。脚本不做全套 XSD 校验、机械验证、Sysmac 导入或编译。

轴引用 contract 示例（名称和轴号只是演示）：

```json
{
  "programs": {
    "Motion": {
      "AxisFeed": {
        "type": "_sAXIS_REF",
        "constant": true,
        "at": "_MC_AX[2]"
      }
    }
  }
}
```

contract 必须来自目标全局变量表/已读取工程及工艺依赖，不能抄待检查 XML 来自证正确。每个需引用轴的 POU 都应列出该引用；不因外部声明缺失就从 contract 省略。constant 按实际属性填写，不统一写 true。AT 必须先核对轴及任务，工具只检查其已提供，不验证运行工程里真实存在该绑定。

## 已发生错误 → 可重复的检查

|失败|原因|防止重复的方法|
|AML 的 ExternalInterface / InternalElement 无效|生成器将接口和模块追加在 SupportedRoleClass 后|检查子元素顺序；相同分组的模块顺序不可改变；仍需完整 XSD 与目标导入|
|轴最大速度换算超限|更改 pulse/mm 后沿用不匹配的默认速度|要求速度参数存在，按比例换算并与目标上限比较；程序命令与轴上限另行核对|
|命名轴和系统轴都报未定义|生成正文时没有补齐 POU 外部声明；只改名字无效|从目标轴绑定建立 contract，检查每个必要外部引用是否声明|
|外部/全局常量属性不匹配|ExternalVars 省略 constant 后默认 false，并非继承全局属性|比较目标属性和声明；保持原全局绑定，修正外部声明|

这些检查不是承诺以后不会出错，而是把已暴露的问题变成可运行的检查项。新错误先保存实际诊断，再补必要检查，不把每次修复堆成互相矛盾的默认规则。
