import os


def str2bool(v):
    return v.lower() in ("true", "yes", "1")


def load_env_file(file_name='legacy'):
    f = open('/srv/app/powerdnsadmin/env/' + file_name + '.env', 'r')
    lines = f.read().splitlines()
    f.close()
    return lines


def load_config_from_env(app):
    legacy_vars = load_env_file('legacy')
    boolean_vars = load_env_file('boolean')
    integer_vars = load_env_file('integer')
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

