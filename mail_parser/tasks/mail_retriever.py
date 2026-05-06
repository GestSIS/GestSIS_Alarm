import imaplib
import email
from pathlib import Path
import uuid
from django.conf import settings
import os.path
from datetime import datetime


class MailRetriever:
    _imap_connection = None
    _mail_whitelist = []

    def __init__(
        self,
        mail_server: str,
        port: int,
        username: str,
        password: str,
        mail_whitelist: list,
        use_starttls=False,
    ):
        if (
            use_starttls
        ):  # Use StartTLS -> Unencrypted IMAP connection then request to encrypt with starttls
            self._imap_connection = imaplib.IMAP4(mail_server, port)
            self._imap_connection.starttls()
        else:  # IMAPs -> IMAP over SSL/TLS (The connection is encrypted from the start
            self._imap_connection = imaplib.IMAP4_SSL(mail_server, port)

        self._imap_connection.login(username, password)

        self._mail_whitelist = [m.lower() for m in mail_whitelist]

    def check_for_new_messages(self, delete_on_read=False, include_read=False, limit=None):
        """
        Scan the inbox for new message that has a PDF attachment and download it on the disk
        :param
          delete_on_read: bool
            If the message should be delete on the server after it has retrieve the PDF
          include_read: bool
            If True, retrieve all messages (read and unread). If False, only unread messages.
          limit: int or None
            Maximum number of messages to retrieve. If None, retrieve all matching messages.

        :return: A list of filename of all the attachment downloaded
        :rtype: list
        """
        new_attachments = []

        messages_list = self._retrieve_messages(include_read=include_read, limit=limit)
        for mail in messages_list:
            new_files = self._save_attachment(mail[1])
            if delete_on_read and len(new_files) > 0:
                self._imap_connection.store(mail[0], "+FLAGS", "\\Deleted")
            else:
                res = self._imap_connection.store(mail[0], '+FLAGS', "\\Seen")
                print("Seen flag res :")
                print(res)

            new_attachments += new_files

        return new_attachments

    def _retrieve_messages(self, include_read=False, limit=None):
        """
        Scan for all the unread message in the inbox, check if they met the condition and return them
        :param
          include_read: bool
            If True, retrieve all messages. If False, only unread messages.
          limit: int or None
            Maximum number of messages to retrieve. If None, retrieve all matching messages.
        :return: A list of tuple containing the mail id as first member and the message object as the second
        :rtype: list
        """
        status, messages = self._imap_connection.select("INBOX")
        
        # Search for all messages or only unread ones
        search_criteria = "ALL" if include_read else "UnSeen"
        search_status, data = self._imap_connection.search(None, search_criteria)

        mail_list = []

        # Shouldn't have to check the data field, but some servers don't play by the rules
        if search_status != "OK" or not data or not data[0]:
            return []

        mail_ids = data[0].split()
        
        # Apply limit: take the last N messages (most recent)
        if limit is not None and limit > 0:
            mail_ids = mail_ids[-limit:]

        for mail_id in mail_ids:
            content = self._fetch_message(mail_id)
            if content is not None:
                mail_list.append((mail_id, content))

        return mail_list

    def _fetch_message(self, mail_id: int):
        """
        Fetch a message from its id and verify that it met the following condition :
            - Has a attachment
            - Is from an address that is in the whitelist

        :param
          mail_id: int
            The ID that the mail has in the inbox

        :return: The message or None if the message doesn't met the criteria
        :rtype: email.message.Message or None
        """
        status, data = self._imap_connection.fetch(mail_id, "(RFC822)")

        # Shouldn't have to check the data field, but some servers don't play by the rules
        if status != "OK" or not data or not data[0]:
            return None

        response_part = data[0][1]

        message = email.message_from_bytes(response_part, policy=email.policy.default)

        if "from" not in message:
            return None  # Shouldn't happen, but better to be sure

        # Discard message if there is no attachment for us
        if message.get_content_maintype() != "multipart":
            return None

        mail_from = message["from"]

        # Check if mail address is in the whitelist
        if email.utils.parseaddr(mail_from)[1].lower() not in self._mail_whitelist:
            return None

        return message

    @staticmethod
    def _save_attachment(msg: email.message.Message):
        """
        Check if there is a PDF as attachment in the message and save it on the disk
        :param
          msg: email.message.Message
            The message where a pdf attachment is
        :return: A list of filename that the method downloaded from the message
        :rtype: list
        """
        filenames = []

        for part in msg.walk():
            # Check if we have a PDF (The extension check is here to be extra sure)

            if (
                part.get_content_type()
                in ["application/pdf", "application/octet-stream"]
                and Path(part.get_filename().strip()).suffix == ".pdf"
            ):
                filename = (
                    datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                    + "_"
                    + str(uuid.uuid4())
                    + ".pdf"
                )
                filepath = os.path.join(settings.MEDIA_ROOT, "pdf", filename)

                with open(filepath, "wb") as fp:
                    fp.write(part.get_payload(decode=True))

                filenames.append(filename)

        return filenames
