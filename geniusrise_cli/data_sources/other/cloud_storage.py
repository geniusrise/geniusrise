import subprocess
from geniusrise_cli.data_sources.batch_data_fetcher import BatchDataFetcher


class RcloneDataFetcher(BatchDataFetcher):
    """
    A batch data fetcher for rclone supported storage providers.
    """

    def __init__(self, provider: str, folder_name: str = "/", handler=None, state_manager=None):
        """
        Initialize the RcloneDataFetcher.

        :param provider: The name of the storage provider configured in rclone.
        :param handler: An optional callable to handle the fetched data.
        :param state_manager: A state manager instance for saving and retrieving state.
        """
        super().__init__(handler, state_manager)
        self.provider = provider
        self.folder_name = folder_name

    def fetch_data(self):
        """
        Fetch data from the remote storage provider.
        """
        try:
            # Run the rclone command to sync data from the remote provider to the output folder
            subprocess.run(["rclone", "sync", f"{self.provider}:/{self.folder_name}", self.output_folder], check=True)
            self.update_state("success")
        except subprocess.CalledProcessError as e:
            self.log.error(f"Error fetching data: {e}")
            self.update_state("failure")

    def __repr__(self) -> str:
        """
        Return a string representation of the batch data fetcher.

        :return: A string representation of the batch data fetcher.
        """
        return f"Rclone data fetcher for {self.provider}: {self.__class__.__name__}"


class AkamaiNetstorageDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("akamai", handler, state_manager)


class AmazonS3DataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("s3", handler, state_manager)


class BoxDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("box", handler, state_manager)


class CloudflareR2DataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("cloudflare", handler, state_manager)


class DigitalOceanSpacesDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("digitalocean", handler, state_manager)


class CitrixShareFileDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("citrix", handler, state_manager)


class FTPDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("ftp", handler, state_manager)


class DropboxDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("dropbox", handler, state_manager)


class GoogleDriveDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("gdrive", handler, state_manager)


class GoogleCloudStorageDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("gcloud", handler, state_manager)


class OpenDriveDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("opendrive", handler, state_manager)


class SFTPDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("sftp", handler, state_manager)


class WebDAVDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("webdav", handler, state_manager)


class ZohoWorkDriveDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("zoho", handler, state_manager)


class MicrosoftOneDriveDataFetcher(RcloneDataFetcher):
    def __init__(self, handler=None, state_manager=None):
        super().__init__("onedrive", handler, state_manager)
