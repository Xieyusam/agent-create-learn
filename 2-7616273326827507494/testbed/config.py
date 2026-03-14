import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Union
from pydantic import BaseModel
from dotenv import load_dotenv


class ModelConfig(BaseModel):
    """模型配置"""
    api_key: str
    model: str
    base_url: str
    temperature: float = 0.1


class AppConfig(BaseModel):
    """应用配置"""
    current_model: str
    models: Dict[str, ModelConfig]
    
    @property
    def current_model_config(self) -> ModelConfig:
        """获取当前使用的模型配置"""
        return self.models[self.current_model]


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """加载配置文件，支持 .env 与 ${ENV_NAME} 占位符"""
    # 加载 .env（若存在）
    _load_env()
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_data: Dict[str, Any] = yaml.safe_load(f)
    
    # 解析占位符
    resolved = _resolve_env_placeholders(config_data)
    
    return AppConfig(**resolved)


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _load_env() -> None:
    """尝试从项目根目录与当前目录加载 .env"""
    # 优先项目根目录（上级）与当前目录
    candidates = [
        Path(".env"),
        Path("..") / ".env",
    ]
    for p in candidates:
        try:
            if p.exists():
                load_dotenv(dotenv_path=p, override=False)
                break
        except Exception:
            # 静默失败，不暴露潜在敏感信息
            pass


def _resolve_env_placeholders(data: Union[Dict[str, Any], list, str, int, float, None]) -> Union[Dict[str, Any], list, str, int, float, None]:
    """递归解析 dict/list 中的 ${ENV_NAME} 占位符"""
    if isinstance(data, dict):
        return {k: _resolve_env_placeholders(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_resolve_env_placeholders(v) for v in data]
    if isinstance(data, str):
        def repl(match: re.Match) -> str:
            env_name = match.group(1)
            val = os.getenv(env_name)
            if val is None:
                raise ValueError(f"缺失必需的环境变量: {env_name}")
            return val
        return _ENV_PATTERN.sub(repl, data)
    return data
