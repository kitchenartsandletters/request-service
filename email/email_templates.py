def build_signed_copy_email(row: dict, token: str) -> str:
    first_name = row.get("first_name") or ""
    greeting = f"Dear {first_name}," if first_name else "Hello,"

    base_url = "https://www.kitchenartsandletters.com/pages/signed-copy-response"

    def link(r):
        return f"{base_url}?t={token}&r={r}"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height:1.5;">
      <p>{greeting}</p>

      <p>
        When you placed your preorder, you were excited about this book. And we were excited to get it to you.
        But I've been following the recent news about co-author René Redzepi, and I don’t feel right sending
        out copies without checking in first.
      </p>

      <p>
        I'd rather know if your feelings about the book have changed than have you receive something you wish
        you hadn't ordered. That's why I’m writing to every preorder customer individually.
      </p>

      <p>Please choose one of the options below:</p>

      <div style="margin:20px 0;">
        <a href="{link('keep')}" style="display:block; padding:12px; background:#111; color:#fff; text-decoration:none; margin-bottom:8px;">
          Keep my order (signed copy)
        </a>

        <a href="{link('unsigned')}" style="display:block; padding:12px; background:#444; color:#fff; text-decoration:none; margin-bottom:8px;">
          Send me an unsigned copy
        </a>

        <a href="{link('cancel')}" style="display:block; padding:12px; background:#999; color:#fff; text-decoration:none;">
          Cancel my order for a full refund
        </a>
      </div>

      <p>
        If we don’t hear from you by March 20, we’ll proceed with your signed copy.
      </p>

      <p>Thank you for being a Kitchen Arts & Letters customer.</p>
    </body>
    </html>
    """