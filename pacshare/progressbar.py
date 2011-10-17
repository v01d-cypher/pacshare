import subprocess
import sys
 
class ProgressBar(object):
    def __init__(self, max_value=None, display_width=None, **kwargs):
        self.started = False
        self.max = max_value

        if not display_width:
            # get terminal row and column size
            term_rows = None
            term_columns = None
            try:
                term_rows, term_columns = map(int, subprocess.check_output(['stty', 'size']).split())
            except subprocess.CalledProcessError as e:
                pass

        self.display_width = (display_width or term_columns or 80)
        self.progress_char = kwargs.get('char', '#')
        self.filename = kwargs.get('filename', '')

        self.f = sys.stdout
 
    def update(self, block_count, block_size, total_size=0):
        if block_count:
            if self.max is None:
                self.max = total_size

            self.render_progress(block_count * block_size)

    def render_heading(self, **kwargs):
        heading = kwargs.get('heading', '')
        if heading:
            heading = '\n{}\n'.format(heading)
            self.f.write(heading)

    def render_progress(self, amount):
        percent_done = round((amount / self.max) * 100)

        # let the progress bar plus extra chars take up 50% of total terminal width
        progress_bar_length = round((50 * self.display_width) / 100) - 7 # (-7 for extra chars: [] 000%)

        # how many chars represent the current percentage done
        num_chars = round((percent_done * progress_bar_length) / 100)
        progress_info = '[{:<{}}] {:>4.0%}'.format(self.progress_char * num_chars, progress_bar_length, amount / self.max)

        remaining_space = self.display_width - len(progress_info) - 2 # (-2 for spaces in front and back)
        filename_info = '{:<{}}'.format(self.filename, remaining_space)

        download_info = ' {}{} '.format(filename_info, progress_info)
 
        self.f.write(download_info + '\r')
        self.f.flush()

        if amount >= self.max:
            self.f.write("\n")
 
def main():
    from time import sleep
    filesize = 4096000
    pb=ProgressBar(filename='test.py')
    blocksize = 4096
    blockcount = 0
    while (blockcount*blocksize) <= filesize:
        pb.update(blockcount, blocksize, filesize)
        sleep(0.002)
        blockcount += 1
 
 
if __name__ == '__main__':
    main()
