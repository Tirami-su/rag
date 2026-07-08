import os
from typing import Optional
from openai import OpenAI
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    api_key: str
    base_url: str
    model: str
    client: Optional[OpenAI] = None


config = {
    "nvidia_deepseek_v4_pro": ProviderConfig(
        api_key=os.environ["NV_API_KEY"],
        model="deepseek-ai/deepseek-v4-pro",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
    "nvidia_deepseek_v4_flash": ProviderConfig(
        api_key=os.environ["NV_API_KEY"],
        model="deepseek-ai/deepseek-v4-flash",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
    "nvidia_minimax-m3": ProviderConfig(
        api_key=os.environ["NV_API_KEY"],
        model="minimaxai/minimax-m3",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
    "nvidia_step-3.7-flash": ProviderConfig(
        api_key=os.environ["NV_API_KEY"],
        model="stepfun-ai/step-3.7-flash",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
    "glm-5.2": ProviderConfig(
        api_key=os.environ["GLM_API_KEY"],
        model="glm-5.2",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    ),
    "glm-4.5-air": ProviderConfig(
        api_key=os.environ["GLM_API_KEY"],
        model="glm-4.5-air",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    ),
    "glm-4.7-flash": ProviderConfig(
        api_key=os.environ["GLM_API_KEY"],
        model="glm-4.7-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
    ),
    "qwen-embedding": ProviderConfig(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model="text-embedding-v4",
        base_url="https://ws-vhe9swyzqj6ff5zp.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    ),
    "qwen3.7-max": ProviderConfig(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model="qwen3.7-max",
        base_url="https://ws-vhe9swyzqj6ff5zp.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    ),
    "qwen3.5-flash": ProviderConfig(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model="qwen3.5-flash",
        base_url="https://ws-vhe9swyzqj6ff5zp.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    ),
    "agnes": ProviderConfig(
        api_key=os.environ["AGNES_API_KEY"],
        model="agnes-2.0-flash",
        base_url="https://apihub.agnes-ai.com/v1",
    ),
}

for key, cfg in config.items():
    cfg.client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
