def player_in_game(player_id, game):
    return player_id == str(game.host.id) or (
        game.guest and player_id == str(game.guest.id)
    )
