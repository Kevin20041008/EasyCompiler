import re

# 词法分析器 - 将源代码转换为标记流
class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []
        
        # 定义关键字和符号
        self.keywords = {'int', 'return', 'if', 'else', 'while'}
        self.symbols = {'=', ';', '(', ')', '{', '}', '+', '-', '*', '/', '<', '>', '==', '!='}
        
    def tokenize(self):
        while self.pos < len(self.code):
            # 跳过空白字符
            if self.code[self.pos].isspace():
                self.pos += 1
                continue
                
            # 识别标识符和关键字
            if self.code[self.pos].isalpha():
                start = self.pos
                while self.pos < len(self.code) and (self.code[self.pos].isalnum() or self.code[self.pos] == '_'):
                    self.pos += 1
                token_value = self.code[start:self.pos]
                if token_value in self.keywords:
                    self.tokens.append(('KEYWORD', token_value))
                else:
                    self.tokens.append(('IDENTIFIER', token_value))
                continue
                
            # 识别数字
            if self.code[self.pos].isdigit():
                start = self.pos
                while self.pos < len(self.code) and self.code[self.pos].isdigit():
                    self.pos += 1
                self.tokens.append(('NUMBER', self.code[start:self.pos]))
                continue
                
            # 识别符号
            for sym in sorted(self.symbols, key=len, reverse=True):
                if self.code.startswith(sym, self.pos):
                    self.tokens.append(('SYMBOL', sym))
                    self.pos += len(sym)
                    break
            else:
                raise Exception(f"未知字符: {self.code[self.pos]}")
                
        return self.tokens

# 语法分析器 - 构建抽象语法树(AST)
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        
    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
        
    def eat(self, token_type, value=None):
        token = self.current_token()
        if token is None:
            raise Exception("意外的文件结尾")
        if token[0] != token_type or (value is not None and token[1] != value):
            raise Exception(f"语法错误: 期望 {token_type}({value}), 但得到 {token[0]}({token[1]})")
        self.pos += 1
        return token
        
    def parse(self):
        return self.parse_program()
        
    def parse_program(self):
        functions = []
        while self.current_token() and self.current_token()[1] == 'int':
            functions.append(self.parse_function())
        return {'type': 'program', 'functions': functions}
        
    def parse_function(self):
        self.eat('KEYWORD', 'int')
        func_name = self.eat('IDENTIFIER')[1]
        self.eat('SYMBOL', '(')
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        
        statements = []
        while self.current_token() and self.current_token()[1] != '}':
            statements.append(self.parse_statement())
            
        self.eat('SYMBOL', '}')
        return {'type': 'function', 'name': func_name, 'body': statements}
        
    def parse_statement(self):
        token = self.current_token()
        if token[0] == 'KEYWORD' and token[1] == 'return':
            return self.parse_return()
        elif token[0] == 'KEYWORD' and token[1] == 'int':
            return self.parse_declaration()
        elif token[0] == 'IDENTIFIER' and self.tokens[self.pos + 1][1] == '=':
            return self.parse_assignment()
        elif token[0] == 'KEYWORD' and token[1] == 'if':
            return self.parse_if()
        elif token[0] == 'KEYWORD' and token[1] == 'while':
            return self.parse_while()
        else:
            raise Exception(f"未知语句: {token[1]}")
            
    def parse_return(self):
        self.eat('KEYWORD', 'return')
        expr = self.parse_expression()
        self.eat('SYMBOL', ';')
        return {'type': 'return', 'expression': expr}
        
    def parse_declaration(self):
        self.eat('KEYWORD', 'int')
        var_name = self.eat('IDENTIFIER')[1]
        self.eat('SYMBOL', ';')
        return {'type': 'declaration', 'name': var_name}
        
    def parse_assignment(self):
        var_name = self.eat('IDENTIFIER')[1]
        self.eat('SYMBOL', '=')
        expr = self.parse_expression()
        self.eat('SYMBOL', ';')
        return {'type': 'assignment', 'name': var_name, 'expression': expr}
        
    def parse_if(self):
        self.eat('KEYWORD', 'if')
        self.eat('SYMBOL', '(')
        condition = self.parse_expression()
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        
        then_block = []
        while self.current_token() and self.current_token()[1] != '}':
            then_block.append(self.parse_statement())
            
        self.eat('SYMBOL', '}')
        
        else_block = []
        if self.current_token() and self.current_token()[1] == 'else':
            self.eat('KEYWORD', 'else')
            self.eat('SYMBOL', '{')
            while self.current_token() and self.current_token()[1] != '}':
                else_block.append(self.parse_statement())
            self.eat('SYMBOL', '}')
            
        return {'type': 'if', 'condition': condition, 'then': then_block, 'else': else_block}
        
    def parse_while(self):
        self.eat('KEYWORD', 'while')
        self.eat('SYMBOL', '(')
        condition = self.parse_expression()
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        
        body = []
        while self.current_token() and self.current_token()[1] != '}':
            body.append(self.parse_statement())
            
        self.eat('SYMBOL', '}')
        return {'type': 'while', 'condition': condition, 'body': body}
        
    def parse_expression(self):
        return self.parse_comparison()
        
    def parse_comparison(self):
        left = self.parse_addition()
        
        while self.current_token() and self.current_token()[1] in ('==', '!=', '<', '>', '<=', '>='):
            op = self.eat('SYMBOL')[1]
            right = self.parse_addition()
            left = {'type': 'binary_operation', 'op': op, 'left': left, 'right': right}
            
        return left
        
    def parse_addition(self):
        left = self.parse_multiplication()
        
        while self.current_token() and self.current_token()[1] in ('+', '-'):
            op = self.eat('SYMBOL')[1]
            right = self.parse_multiplication()
            left = {'type': 'binary_operation', 'op': op, 'left': left, 'right': right}
            
        return left
        
    def parse_multiplication(self):
        left = self.parse_primary()
        
        while self.current_token() and self.current_token()[1] in ('*', '/'):
            op = self.eat('SYMBOL')[1]
            right = self.parse_primary()
            left = {'type': 'binary_operation', 'op': op, 'left': left, 'right': right}
            
        return left
        
    def parse_primary(self):
        token = self.current_token()
        if token[0] == 'NUMBER':
            self.eat('NUMBER')
            return {'type': 'number', 'value': int(token[1])}
        elif token[0] == 'IDENTIFIER':
            self.eat('IDENTIFIER')
            return {'type': 'variable', 'name': token[1]}
        elif token[1] == '(':
            self.eat('SYMBOL', '(')
            expr = self.parse_expression()
            self.eat('SYMBOL', ')')
            return expr
        else:
            raise Exception(f"意外的标记: {token[1]}")

# 代码生成器 - 生成x86汇编代码
class CodeGenerator:
    def __init__(self):
        self.variables = set()
        self.label_counter = 0
        self.code = []
        
    def generate_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"
        
    def generate(self, ast):
        if ast['type'] == 'program':
            self.code.append(".section .text")
            self.code.append(".globl _start")
            self.code.append("")
            
            for func in ast['functions']:
                self.generate_function(func)
                
            return "\n".join(self.code)
            
    def generate_function(self, func):
        if func['name'] == 'main':
            self.code.append("_start:")
        else:
            self.code.append(f"{func['name']}:")
            
        # 函数序言
        self.code.append("push %ebp")
        self.code.append("mov %esp, %ebp")
        
        # 为局部变量分配空间
        local_vars = set()
        for stmt in func['body']:
            if stmt['type'] == 'declaration':
                local_vars.add(stmt['name'])
                
        if local_vars:
            self.code.append(f"sub ${4 * len(local_vars)}, %esp")
            
        # 生成函数体代码
        for stmt in func['body']:
            self.generate_statement(stmt)
            
        # 函数尾声
        self.code.append("mov %ebp, %esp")
        self.code.append("pop %ebp")
        self.code.append("ret")
        self.code.append("")
        
    def generate_statement(self, stmt):
        if stmt['type'] == 'return':
            self.generate_expression(stmt['expression'])
            self.code.append("mov %eax, %ebx")
            self.code.append("mov $1, %eax")
            self.code.append("int $0x80")
        elif stmt['type'] == 'declaration':
            # 变量声明，已经在栈上分配了空间
            pass
        elif stmt['type'] == 'assignment':
            self.generate_expression(stmt['expression'])
            var_offset = self.get_variable_offset(stmt['name'])
            self.code.append(f"mov %eax, {var_offset}(%ebp)")
        elif stmt['type'] == 'if':
            self.generate_if(stmt)
        elif stmt['type'] == 'while':
            self.generate_while(stmt)
            
    def generate_if(self, stmt):
        else_label = self.generate_label()
        end_label = self.generate_label()
        
        # 生成条件表达式
        self.generate_expression(stmt['condition'])
        self.code.append("cmp $0, %eax")
        
        # 如果条件为假，跳转到else或结束
        if stmt['else']:
            self.code.append(f"je {else_label}")
        else:
            self.code.append(f"je {end_label}")
            
        # 生成then块
        for then_stmt in stmt['then']:
            self.generate_statement(then_stmt)
            
        if stmt['else']:
            self.code.append(f"jmp {end_label}")
            self.code.append(f"{else_label}:")
            for else_stmt in stmt['else']:
                self.generate_statement(else_stmt)
                
        self.code.append(f"{end_label}:")
        
    def generate_while(self, stmt):
        start_label = self.generate_label()
        end_label = self.generate_label()
        
        self.code.append(f"{start_label}:")
        
        # 生成条件表达式
        self.generate_expression(stmt['condition'])
        self.code.append("cmp $0, %eax")
        self.code.append(f"je {end_label}")
        
        # 生成循环体
        for body_stmt in stmt['body']:
            self.generate_statement(body_stmt)
            
        self.code.append(f"jmp {start_label}")
        self.code.append(f"{end_label}:")
        
    def generate_expression(self, expr):
        if expr['type'] == 'number':
            self.code.append(f"mov ${expr['value']}, %eax")
        elif expr['type'] == 'variable':
            var_offset = self.get_variable_offset(expr['name'])
            self.code.append(f"mov {var_offset}(%ebp), %eax")
        elif expr['type'] == 'binary_operation':
            self.generate_expression(expr['right'])
            self.code.append("push %eax")
            self.generate_expression(expr['left'])
            self.code.append("pop %ecx")
            
            if expr['op'] == '+':
                self.code.append("add %ecx, %eax")
            elif expr['op'] == '-':
                self.code.append("sub %ecx, %eax")
            elif expr['op'] == '*':
                self.code.append("imul %ecx, %eax")
            elif expr['op'] == '/':
                self.code.append("cdq")
                self.code.append("idiv %ecx")
            elif expr['op'] == '==':
                self.code.append("cmp %ecx, %eax")
                self.code.append("sete %al")
                self.code.append("movzbl %al, %eax")
            elif expr['op'] == '!=':
                self.code.append("cmp %ecx, %eax")
                self.code.append("setne %al")
                self.code.append("movzbl %al, %eax")
            elif expr['op'] == '<':
                self.code.append("cmp %ecx, %eax")
                self.code.append("setl %al")
                self.code.append("movzbl %al, %eax")
            elif expr['op'] == '>':
                self.code.append("cmp %ecx, %eax")
                self.code.append("setg %al")
                self.code.append("movzbl %al, %eax")
                
    def get_variable_offset(self, var_name):
        # 简化处理：假设变量在栈上的偏移量是固定的
        # 在实际编译器中，需要维护一个符号表来跟踪变量位置
        return -4  # 简化处理，所有变量都在ebp-4的位置

# 测试编译器
def test_compiler():
    # 示例源代码
    source_code = """
    int main() {
        int a;
        a = 10 + 5;
        if (a == 15) {
            a = 20;
        } else {
            a = 30;
        }
        return a;
    }
    """
    
    # 词法分析
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print("Tokens:", tokens)
    
    # 语法分析
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST:", ast)
    
    # 代码生成
    generator = CodeGenerator()
    assembly_code = generator.generate(ast)
    print("Generated Assembly:")
    print(assembly_code)

if __name__ == "__main__":
    test_compiler()