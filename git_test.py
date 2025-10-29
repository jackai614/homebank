#!/usr/bin/env python3
"""
Git连接问题诊断工具
用于诊断和修复无法访问GitHub等Git仓库的问题
"""

import subprocess
import sys
import os
import platform
import socket
import requests
import time
from urllib.parse import urlparse

class GitConnectionDiagnostic:
    def __init__(self):
        self.results = []
        self.system = platform.system().lower()
        
    def log_result(self, test_name, status, message, solution=None):
        """记录测试结果"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'solution': solution,
            'timestamp': time.time()
        }
        self.results.append(result)
        
        # 输出彩色结果
        if status == 'PASS':
            print(f"✅ [{test_name}] {message}")
        elif status == 'WARNING':
            print(f"⚠️  [{test_name}] {message}")
        else:
            print(f"❌ [{test_name}] {message}")
            
        if solution:
            print(f"   💡 解决方案: {solution}")
        print()
    
    def check_network_connectivity(self):
        """检查基本网络连接"""
        try:
            # 测试基本网络连接
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            self.log_result("网络连接", "PASS", "基本网络连接正常")
            return True
        except socket.error:
            self.log_result("网络连接", "FAIL", "无法连接到互联网")
            return False
    
    def check_dns_resolution(self, hostname="github.com"):
        """检查DNS解析"""
        try:
            ip_address = socket.gethostbyname(hostname)
            self.log_result("DNS解析", "PASS", f"{hostname} 解析为 {ip_address}")
            return True
        except socket.gaierror:
            self.log_result("DNS解析", "FAIL", f"无法解析主机名: {hostname}",
                          "尝试更换DNS服务器为 8.8.8.8 或 114.114.114.114")
            return False
    
    def check_github_access(self):
        """检查GitHub访问"""
        try:
            response = requests.get("https://github.com", timeout=10)
            if response.status_code == 200:
                self.log_result("GitHub访问", "PASS", "可以正常访问GitHub")
                return True
            else:
                self.log_result("GitHub访问", "WARNING", 
                              f"GitHub返回状态码: {response.status_code}")
                return False
        except requests.RequestException as e:
            self.log_result("GitHub访问", "FAIL", f"无法访问GitHub: {str(e)}")
            return False
    
    def check_git_config(self):
        """检查Git配置"""
        try:
            # 检查Git是否安装
            result = subprocess.run(["git", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                self.log_result("Git安装", "FAIL", "Git未安装或不在PATH中",
                              "请安装Git: https://git-scm.com/downloads")
                return False
            
            self.log_result("Git安装", "PASS", f"Git版本: {result.stdout.strip()}")
            
            # 检查Git配置
            config_checks = [
                ("user.name", "用户名"),
                ("user.email", "邮箱"),
                ("http.sslVerify", "SSL验证")
            ]
            
            for config_key, desc in config_checks:
                result = subprocess.run(["git", "config", "--global", config_key],
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_result(f"Git配置-{desc}", "PASS", 
                                  f"{config_key} = {result.stdout.strip()}")
                else:
                    self.log_result(f"Git配置-{desc}", "WARNING", 
                                  f"{config_key} 未设置")
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_result("Git安装", "FAIL", "Git命令执行失败")
            return False
    
    def check_proxy_settings(self):
        """检查代理设置"""
        env_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
        found_proxy = False
        
        for var in env_vars:
            if os.environ.get(var):
                self.log_result("代理设置", "WARNING", 
                              f"检测到代理设置: {var}={os.environ[var]}")
                found_proxy = True
        
        if not found_proxy:
            self.log_result("代理设置", "PASS", "未检测到代理设置")
        
        return not found_proxy
    
    def test_git_operations(self, repo_url):
        """测试Git操作"""
        test_dir = "git_test_temp"
        
        try:
            # 清理之前的测试目录
            if os.path.exists(test_dir):
                subprocess.run(["rm", "-rf", test_dir], capture_output=True)
            
            # 测试git clone
            print(f"正在测试克隆仓库: {repo_url}")
            result = subprocess.run(["git", "clone", repo_url, test_dir],
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.log_result("Git克隆", "PASS", "仓库克隆成功")
                # 清理测试目录
                subprocess.run(["rm", "-rf", test_dir], capture_output=True)
                return True
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.log_result("Git克隆", "FAIL", f"克隆失败: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_result("Git克隆", "FAIL", "克隆操作超时")
            return False
        except Exception as e:
            self.log_result("Git克隆", "FAIL", f"克隆异常: {str(e)}")
            return False
    
    def suggest_solutions(self):
        """根据检测结果提供解决方案"""
        print("\n" + "="*60)
        print("📋 诊断报告和解决方案")
        print("="*60)
        
        fails = [r for r in self.results if r['status'] == 'FAIL']
        warnings = [r for r in self.results if r['status'] == 'WARNING']
        
        if not fails and not warnings:
            print("🎉 所有检查通过！Git连接正常。")
            return
        
        if fails:
            print("\n❌ 需要立即解决的问题:")
            for fail in fails:
                print(f"  • {fail['test']}: {fail['message']}")
                if fail['solution']:
                    print(f"    → {fail['solution']}")
        
        if warnings:
            print("\n⚠️  建议优化的项目:")
            for warn in warnings:
                print(f"  • {warn['test']}: {warn['message']}")
                if warn['solution']:
                    print(f"    → {warn['solution']}")
        
        print("\n🔧 通用解决方案:")
        print("1. 检查网络连接和防火墙设置")
        print("2. 尝试更换DNS服务器 (如 8.8.8.8 或 114.114.114.114)")
        print("3. 临时关闭代理设置: unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY")
        print("4. 使用SSH替代HTTPS: git@github.com:user/repo.git")
        print("5. 使用GitHub镜像站点")
    
    def run_full_diagnosis(self, repo_url=None):
        """运行完整诊断"""
        print("🔍 开始Git连接诊断...")
        print("="*60)
        
        # 执行各项检查
        self.check_network_connectivity()
        self.check_dns_resolution()
        self.check_github_access()
        self.check_git_config()
        self.check_proxy_settings()
        
        # 如果提供了仓库URL，测试具体操作
        if repo_url:
            self.test_git_operations(repo_url)
        
        # 提供解决方案
        self.suggest_solutions()

def main():
    """主函数"""
    diagnostic = GitConnectionDiagnostic()
    
    # 默认测试GitHub，或使用用户提供的URL
    test_url = "https://github.com/jackai614/homebank.git"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    print(f"目标仓库: {test_url}")
    diagnostic.run_full_diagnosis(test_url)

if __name__ == "__main__":
    main()
