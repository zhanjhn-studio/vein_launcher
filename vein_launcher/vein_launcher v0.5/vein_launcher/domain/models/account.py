"""账号模型 - 离线 / 微软正版双支持"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class AccountBase(ABC, BaseModel):
    """账号基类（抽象）"""
    
    account_id: str = Field(..., description="账号唯一标识")
    username: str = Field(..., description="游戏用户名（显示名）")
    selected: bool = Field(default=False, description="是否当前选中")
    
    @abstractmethod
    def is_valid(self) -> bool:
        """验证账号是否有效"""
        pass
    
    @abstractmethod
    def get_auth_token(self) -> Optional[str]:
        """获取认证 token（微软账号返回 JWT，离线账号无）"""
        pass


class OfflineAccount(AccountBase):
    """离线模式账号 - 无需登录验证"""
    
    account_type: Literal["offline"] = Field(default="offline", description="离线账号标记")
    # username + account_id 就足够
    
    def is_valid(self) -> bool:
        """离线账号只要用户名非空即有效"""
        return bool(self.username and len(self.username) >= 3 and len(self.username) <= 16)
    
    def get_auth_token(self) -> Optional[str]:
        """离线账号返回 None"""
        return None


class MicrosoftAccount(AccountBase):
    """微软正版账号 - OAuth2 流程认证"""
    
    account_type: Literal["microsoft"] = Field(default="microsoft", description="微软账号标记")

    # Minecraft 档案信息
    uuid: Optional[str] = Field(default=None, description="Minecraft 档案 UUID（无破折号）")
    
    # OAuth2 相关 token（刷新机制）
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[int] = None  # Unix timestamp
    
    # Xbox Live Token
    xbl_token: Optional[str] = None
    xui_token: Optional[Dict[str, Any]] = None  # Xbox User Identity JSON
    
    # Minecraft 服务器端 token（YSER）
    mc_access_token: Optional[str] = None
    mc_expires_at: Optional[int] = None  # Minecraft 会话 token 到期时间（Unix timestamp）
    mc_selected_profile: Optional[str] = None  # UUID（无破折号版）
    
    def is_valid(self) -> bool:
        """验证微软账号是否已登录且有效期内"""
        if not self.access_token:
            return False
        
        import time
        current_time = int(time.time())
        
        # 检查 token 是否过期（提前 5 分钟刷新）
        if self.token_expires_at and current_time + 300 > self.token_expires_at:
            return False
            
        # 必须有 Xbox Live token
        if not self.xbl_token:
            return False
            
        return True
    
    def get_auth_token(self) -> Optional[str]:
        """返回 Microsoft Access Token（用于登录 YSER）"""
        return self.mc_access_token
    
    def needs_refresh(self) -> bool:
        """检查是否需要刷新 token"""
        if not self.token_expires_at:
            return True
        
        import time
        current_time = int(time.time())
        
        # 过期前 10 分钟触发刷新
        return current_time + 600 > self.token_expires_at


class LittleSkinAccount(AccountBase):
    """LittleSkin（及兼容 Yggdrasil 的皮肤站）账号"""

    account_type: Literal["littleskin"] = Field(
        default="littleskin", description="皮肤站账号标记"
    )

    server: str = Field(
        default="https://littleskin.cn/api/yggdrasil", description="皮肤站 Yggdrasil API 根地址"
    )
    uuid: Optional[str] = None
    access_token: Optional[str] = None
    client_token: Optional[str] = None
    skin_model: Optional[str] = None  # slim / classic

    def is_valid(self) -> bool:
        return bool(self.access_token and self.uuid)

    def get_auth_token(self) -> Optional[str]:
        return self.access_token


REFRESH_MARGIN = 600  # 提前 10 分钟续期，避免启动瞬间过期


def token_needs_refresh(expires_at: Optional[int], now: Optional[int] = None,
                        margin: int = REFRESH_MARGIN) -> bool:
    """判断 Minecraft 会话 token 是否需要续期（纯函数，便于测试）"""
    if not expires_at:
        return True
    import time as _time

    current = int(now if now is not None else _time.time())
    return current + margin >= int(expires_at)


class AccountManager(BaseModel):
    """账号管理器（多账号支持）"""    
    accounts: list[AccountBase] = Field(default_factory=list)
    selected_account_id: Optional[str] = None
    
    def add_account(self, account: AccountBase) -> None:
        """添加账号"""
        self.accounts.append(account)
        if not self.selected_account_id:
            self.selected_account_id = account.account_id
    
    def remove_account(self, account_id: str) -> bool:
        """删除账号"""
        for i, acc in enumerate(self.accounts):
            if acc.account_id == account_id:
                del self.accounts[i]
                # 如果删除的是当前选中，取消选择
                if self.selected_account_id == account_id:
                    self.selected_account_id = None
                return True
        return False
    
    def get_selected_account(self) -> Optional[AccountBase]:
        """获取当前选中的账号"""
        for acc in self.accounts:
            if acc.account_id == self.selected_account_id:
                return acc
        return None
    
    def select_account(self, account_id: str) -> bool:
        """切换选中账号"""
        if any(acc.account_id == account_id for acc in self.accounts):
            self.selected_account_id = account_id
            return True
        return False
