from tengi import CommandParam, tengi_command_params

# Note: channel_id, reactions, post_link are NOT registered here
# because our handler parses them directly from raw message text.
# This prevents tengi from rejecting commands with custom format.
command_params = tengi_command_params.params + [
    CommandParam(name='--message_id',
                 help_str='Message id',
                 param_type=int),
    CommandParam(name='--bot_token',
                 help_str='Bot token',
                 param_type=str),
    CommandParam(name='--n',
                 help_str='N items to take',
                 param_type=int),
]
