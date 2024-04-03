def chunk_str(blurb, size):
    """Breaks string up (on whitespace) by chunk size."""
    if len(blurb) > size:
        all_chunks = []
        current_line = ""
        words = blurb.split(" ")

        for word in words:
            # If str wouldn't exceed chunk size:
            if (len(current_line) + len(word) + 1) < size:
                # If its the initial, empty line.
                if current_line == "":
                    current_line = str(word)
                # Otherwise append + space.
                else:
                    current_line += " "+str(word)
            # Otherwise, start a new chunk
            else:
                all_chunks.append(current_line)
                current_line = str(word)

        # Append last chunk segment.
        all_chunks.append(current_line)

        return all_chunks

    return [blurb]