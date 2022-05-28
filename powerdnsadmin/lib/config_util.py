import os


def str2bool(v) -> bool:
    return v.lower() in ("true", "yes", "1")


def load_env_file(env_path: str, file_name: str = 'legacy') -> list:
    f = open(f'{env_path}{file_name}.env', 'r')
    lines = f.read().splitlines()
    f.close()
    return lines


def load_config_from_env(app, root_path: str) -> None:
    if root_path[-1] != '/':
        root_path += '/'
    env_path = f'{root_path}powerdnsadmin/env/'
    legacy_vars = load_env_file(env_path, 'legacy')
    boolean_vars = load_env_file(env_path, 'boolean')
    integer_vars = load_env_file(env_path, 'integer')
    config = {}

    for key in os.environ:
        config_key = None
        val = None

        if (key.startswith('PDA_') or key in legacy_vars) and not key.endswith('_FILE'):
            config_key = key
            val = os.environ[key]

        if key.startswith('PDAC_') and not key.endswith('_FILE'):
            config_key = key[5:]
            val = os.environ[key]

        if key.endswith('_FILE'):
            config_key = key[:-5]

            if key.startswith('PDAC_'):
                config_key = config_key[5:]

            if key.startswith('PDAC_') or config_key in legacy_vars:
                with open(os.environ[key]) as f:
                    val = f.read()
                f.close()

        if val is not None:
            if config_key in boolean_vars:
                val = str2bool(val)
            if config_key in integer_vars:
                val = int(val)

        if config_key is not None:
            config[config_key] = val

    if isinstance(config, dict):
        app.config.update(config)

