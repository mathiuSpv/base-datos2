def is_objectid_hex(v: str) -> bool:
  if len(v) != 24:
    return False
  try:
    int(v, 16)
    return True
  except ValueError:
    return False