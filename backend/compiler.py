"""
Code Compiler для проверки Go и Solidity кода
Используется для автоматической проверки решений задач
"""
import subprocess
import tempfile
import os
from typing import Dict, Optional, List
from pathlib import Path
import shutil
import json


class CodeCompiler:
    """Компилятор для проверки кода на Go и Solidity"""
    
    def __init__(self):
        self.temp_dir = None
        self._create_temp_dir()
    
    def _create_temp_dir(self):
        """Создает временную директорию для компиляции"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="claudetests_"))
    
    def cleanup(self):
        """Удаляет временную директорию"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def compile_go(
        self, 
        code: str, 
        test_code: Optional[str] = None,
        timeout: int = 30
    ) -> Dict:
        """
        Компилирует Go код и запускает тесты
        
        Args:
            code: Код для компиляции
            test_code: Опциональный код тестов
            timeout: Таймаут в секундах
        
        Returns:
            Dict с результатами:
            {
                "success": bool,
                "compiled": bool,
                "output": str,
                "errors": List[str],
                "test_results": Optional[Dict],
                "execution_time": float
            }
        """
        result = {
            "success": False,
            "compiled": False,
            "output": "",
            "errors": [],
            "test_results": None,
            "execution_time": 0.0
        }
        
        import time
        start_time = time.time()
        
        try:
            # Создаем временный модуль
            module_dir = self.temp_dir / "go_task"
            module_dir.mkdir(exist_ok=True)
            
            # Инициализируем go mod
            go_mod_result = subprocess.run(
                ["go", "mod", "init", "task"],
                cwd=module_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Создаем main.go
            main_file = module_dir / "main.go"
            main_file.write_text(code, encoding='utf-8')
            
            # Компилируем код
            compile_result = subprocess.run(
                ["go", "build", "-o", str(module_dir / "task"), str(main_file)],
                cwd=module_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result["compiled"] = compile_result.returncode == 0
            result["output"] = compile_result.stdout
            
            if compile_result.returncode != 0:
                # Парсим ошибки компиляции
                error_lines = compile_result.stderr.strip().split("\n")
                result["errors"] = [line for line in error_lines if line.strip()]
                result["execution_time"] = time.time() - start_time
                return result
            
            # Если есть тесты, запускаем их
            if test_code:
                test_file = module_dir / "main_test.go"
                test_file.write_text(test_code, encoding='utf-8')
                
                test_result = subprocess.run(
                    ["go", "test", "-v", "-json"],
                    cwd=module_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Парсим JSON вывод тестов
                test_output_lines = test_result.stdout.strip().split("\n")
                test_events = []
                passed_tests = 0
                failed_tests = 0
                
                for line in test_output_lines:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            test_events.append(event)
                            if event.get("Action") == "pass":
                                passed_tests += 1
                            elif event.get("Action") == "fail":
                                failed_tests += 1
                        except json.JSONDecodeError:
                            pass
                
                result["test_results"] = {
                    "passed": test_result.returncode == 0,
                    "passed_count": passed_tests,
                    "failed_count": failed_tests,
                    "output": test_result.stdout,
                    "stderr": test_result.stderr,
                    "events": test_events
                }
                
                result["success"] = result["test_results"]["passed"]
            else:
                # Если тестов нет, просто проверяем компиляцию
                result["success"] = True
            
            result["execution_time"] = time.time() - start_time
            
        except subprocess.TimeoutExpired:
            result["errors"] = [f"Compilation timeout ({timeout}s)"]
            result["execution_time"] = time.time() - start_time
        except FileNotFoundError:
            result["errors"] = ["Go compiler not found. Make sure Go is installed and in PATH."]
        except Exception as e:
            result["errors"] = [f"Unexpected error: {str(e)}"]
            result["execution_time"] = time.time() - start_time
        
        return result
    
    def compile_solidity(
        self, 
        code: str,
        version: str = "0.8.0",
        timeout: int = 30
    ) -> Dict:
        """
        Компилирует Solidity код
        
        Args:
            code: Solidity код
            version: Версия компилятора
            timeout: Таймаут в секундах
        
        Returns:
            Dict с результатами компиляции
        """
        result = {
            "success": False,
            "compiled": False,
            "output": "",
            "errors": [],
            "abi": None,
            "bytecode": None,
            "execution_time": 0.0
        }
        
        import time
        start_time = time.time()
        
        try:
            # Создаем временный файл
            contract_file = self.temp_dir / "contract.sol"
            contract_file.write_text(code, encoding='utf-8')
            
            # Компилируем через solc
            compile_result = subprocess.run(
                [
                    "solc",
                    "--version", version,
                    "--abi",
                    "--bin",
                    "--optimize",
                    str(contract_file)
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            result["compiled"] = compile_result.returncode == 0
            result["output"] = compile_result.stdout
            
            if compile_result.returncode != 0:
                error_lines = compile_result.stderr.strip().split("\n")
                result["errors"] = [line for line in error_lines if line.strip()]
            else:
                # Парсим ABI и bytecode из вывода
                # Это упрощенная версия, в реальности нужно парсить JSON
                result["success"] = True
            
            result["execution_time"] = time.time() - start_time
            
        except subprocess.TimeoutExpired:
            result["errors"] = [f"Compilation timeout ({timeout}s)"]
        except FileNotFoundError:
            result["errors"] = ["Solc compiler not found. Install solc: npm install -g solc"]
        except Exception as e:
            result["errors"] = [f"Unexpected error: {str(e)}"]
        
        result["execution_time"] = time.time() - start_time
        return result
    
    def check_go_installed(self) -> bool:
        """Проверяет установлен ли Go"""
        try:
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_solc_installed(self) -> bool:
        """Проверяет установлен ли solc"""
        try:
            result = subprocess.run(
                ["solc", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


# Singleton instance
_compiler_instance = None

def get_compiler() -> CodeCompiler:
    """Получить экземпляр компилятора (singleton)"""
    global _compiler_instance
    if _compiler_instance is None:
        _compiler_instance = CodeCompiler()
    return _compiler_instance

