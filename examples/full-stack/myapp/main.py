from pico_boot import init
from pico_ioc import configuration, YamlTreeSource

from .services import UserService


def main():
    config = configuration(YamlTreeSource("application.yaml"))

    container = init(
        modules=["myapp.config", "myapp.services"],
        config=config,
    )

    user_service = container.get(UserService)

    # Get a user profile
    profile = user_service.get_user_profile(1)
    print(f"User profile: {profile}")

    # Update email
    success = user_service.update_email(1, "alice.new@example.com")
    print(f"Email updated: {success}")

    container.shutdown()


if __name__ == "__main__":
    main()
