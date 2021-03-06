from os.path import join, dirname

from creAI import Style, App
import creAI.style

from creAI.mc import Schematic


from creAI.ml.models.dummy import DummyGeneratorNetwork

from creAI.cli import CommandlineInterface, command
creAI.style.STYLES_PATH = join(dirname(__file__), 'test_styles')



class LossTest(CommandlineInterface):
    """Testing feature-loss.

    This is a simple test program for the feature loss implemented in
    creAI/ml/losses/feature_loss.py
    """
    def __init__(self):
        super(LossTest, self).__init__()
        

    @command
    def train(self, style, schem, batch_size=16, epochs=100):
        """Training mode.

        This subcommand optimizes a single tensor for the loss.

        Args:
            style (str): Name of the style.
            schem (str): Path to a schematic file.
            batch_size (int): Batch size.
            epochs (int): Epochs.
        """
        self.stl = Style(style, mc_version='1.15.2')
        self.stl.info['schem_pth'] = schem
        vae = self.stl.models.vae
        self.stl.models.generator = DummyGeneratorNetwork(256, vae.latent_dim, shape=(32,16,32))
        self.stl.models.generator.build()

        self.stl.train(generator=True, schem_pth=schem, 
                        batch_size=batch_size, epochs=epochs)

    @command
    def display(self, style):
        """Display mode.

        Args:
            style (str): Name of the style.
        """
        self.stl = Style(style, mc_version='1.15.2')
        with open(self.stl.info['schem_pth'], 'rb') as schem_file:
            o_tlmp = Schematic.load(schem_file, self.stl.info['mc_version'])

        g_tlmp = self.stl.generate(shape=(64,16,64))

        o_w, o_h, o_l = o_tlmp.shape
        g_w, g_h, g_l = g_tlmp.shape
        spacing = 16
        combined = Schematic(
            shape=(o_w + g_w + spacing, 
                    max(o_h,g_h),
                    max(o_l,g_l),
                    ),
            version=self.stl.info['mc_version']
            )
        
        combined[:o_w,:o_h,:o_l] = o_tlmp
        combined[o_w+spacing:,:g_h,:g_l] = g_tlmp

        app = App()
        app.tlmp = combined
        app.start_gui()

LossTest().run()