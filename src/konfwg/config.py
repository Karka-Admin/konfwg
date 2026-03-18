from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Configuration(BaseSettings):
    """
    base_url: base url
    konfwg_cli_path: /usr/local/bin # holds konfwg cli command that runs the tool
    konfwg_code_path: /opt/konfwg # konfwg code
    konfwg_etc_path: /etc/konfwg # konfwg secrets
    konfwg_db_path: /var/lib/konfwg # konfwg database
    konfwg_log_path: /var/log/konfwg # konfwg logs
    konfwg_tmp_path: /tmp/konfwg # konfwg temporary files (CURRENTLY UNIMPLEMENTED)
    konfwg_sudo_path: /etc/sudoers.d # konfwg sudoers configuration
    wg_directory: /etc/wireguard # wireguard directory
    wg_publicint: public interface of the server
    """
    BASE_URL: str

    CLI_PATH: Path
    CODE_PATH: Path
    ETC_PATH: Path
    DB_PATH: Path
    LOG_PATH: Path
    TMP_PATH: Path
    SUDO_PATH: Path
    WG_DIRECTORY: Path

    WG_PUBLICINT: str
    DEFAULT_TTL: int = 900
    DEFAULT_HITS: int = 1
    SECRET: str

    model_config = SettingsConfigDict(env_file="/etc/konfwg/konfwg.conf")

configuration = Configuration()