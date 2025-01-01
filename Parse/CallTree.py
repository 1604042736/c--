from Basic import Token, Error, Diagnostics


class CallTree:
    """调用树"""

    def __init__(self, name: str, parent: "CallTree", begin_token: Token):
        self.name = name  # 函数名称
        self.depth = 1  # 深度
        self.parent = parent  # 父节点
        self.position = 0  # 在兄弟节点中的位置
        self.begin_token: Token = begin_token  # 调用时的token

        self.return_val = None  # 返回值
        self.args = tuple()
        self.kwargs = dict()
        self.not_none_count = 0  # 该节点之前的连续非None节点处理

        self.mark = False  # 标记错误是否出现在这个节点

        self.children: list[CallTree] = []

    def print(self, indent=0):
        print(
            f"{'  '*indent}{self.name} [{self.mark}] {self.begin_token} ({self.args}, {self.kwargs}): {self.return_val}"
        )
        for child in self.children:
            child.print(indent + 1)

    def get_diagnostic(self):
        if self.name.startswith("expect"):
            return Error(
                f"期待得到'{self.args[0]}'在'{self.begin_token.text}'之前",
                self.begin_token.location,
            )
        return Error(f"{self.name}, {self.args}", self.begin_token.location)


def generate_diagnostic(self: CallTree) -> Diagnostics:
    """生成诊断信息"""
    mark_calltree(self)
    diagnostics = _generate_diagnostic(self)
    return diagnostics


def _generate_diagnostic(self: CallTree) -> Diagnostics:
    """访问调用树节点, 并生成诊断信息, 与generate_diagnostic配合使用"""
    ret = Diagnostics([])
    candidate = []

    for child in self.children:
        if child.mark == True:
            begin = self.begin_token.location[0]
            end = child.begin_token.location[0]
            # 忽略了所处文件
            distance = (end["lineno"] - begin["lineno"], end["col"] - begin["col"])
            candidate.append((child, distance))

    # 选择推导程度最大并且被标记的节点
    candidate.sort(key=lambda x: x[1], reverse=True)
    for i in candidate:
        if i[1] == candidate[0][1]:
            ret += _generate_diagnostic(i[0])

    if not ret and self.mark:
        ret += [self.get_diagnostic()]
    return ret


def mark_calltree(self: CallTree):
    """标记调用树"""
    if self.return_val != None:
        self.mark = False
        return

    not_none_count = 0
    for child in self.children:
        mark_calltree(child)
        if (
            child.name.startswith("optional")
            and child.mark == False
            and child.return_val == None
        ):
            continue
        child.not_none_count = not_none_count
        if child.return_val == None:  # 推导在这次调用中失败
            if not_none_count != 0:  # 这个(非)终结符不是产生式的第一个
                child.mark = True
            not_none_count = 0
        else:
            not_none_count += 1

    self.mark = self.mark or any([child.mark for child in self.children])
