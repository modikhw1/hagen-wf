"""Parametrisk rekvisita. XYZ i meter, Z upp; greppunkt i samma lokala rum.

Form, tjocklek och dolda sidor är mallar, aldrig uppmätta tillgångar.
Tallrik, burk och låda återanvänder den äldre kedjans primitivfamiljer.
"""
import copy

def del_(form, pos, matt, farg):
    return dict(form=form, pos=pos, matt=matt, farg=farg)

PAPPER = del_('lada', [0, 0, -.025], [1, 1, .025], '#f5ede2')
TALLRIK = del_('cylinder', [0, 0, -.03], [1, 1, .08], '#eee9dd')
BANK = {
    'meat_cut': dict(matt=[.38, .26, .09], grepp=[0, 0, -.045], delar=[PAPPER,
        del_('ellipsoid', [0, 0, .12], [.8, .7, .8], '#a93241'),
        del_('ellipsoid', [.12, -.12, .22], [.42, .25, .38], '#e7b5a0')]),
    'weighing_scale': dict(matt=[.32, .30, .45], grepp=[0, 0, -.225], delar=[
        del_('lada', [0, 0, -.38], [1, 1, .18], '#c4c5c0'),
        del_('lada', [0, 0, -.25], [1.05, 1.05, .05], '#e1e1dc'),
        del_('lada', [0, .32, .02], [.07, .07, .7], '#848e91'),
        del_('lada', [0, .32, .34], [1, .10, .30], '#ced8d8'),
        del_('lada', [0, .255, .34], [.83, .025, .20], '#334b48')]),
    'ice_cream_spoon': dict(matt=[.035, .16, .025], grepp=[0, -.05, 0], delar=[
        del_('lada', [0, -.10, 0], [.20, .80, .15], '#e4cdae'),
        del_('ellipsoid', [0, .35, .20], [1, .28, 1], '#c0c787')]),
    'gelato_spatula': dict(matt=[.10, .28, .08], grepp=[0, -.08, -.02], delar=[
        del_('lada', [0, -.10, -.2], [.22, .80, .18], '#a9b1b0'),
        del_('ellipsoid', [0, .28, .15], [1, .46, 1], '#b5c774')]),
    'plate': dict(matt=[.29, .29, .025], grepp=[0, -.11, -.012], delar=[TALLRIK]),
    'can': dict(matt=[.066, .066, .12], grepp=[0, 0, -.06], delar=[
        del_('cylinder', [0, 0, 0], [1, 1, 1], '#e8d44a'),
        del_('cylinder', [0, 0, .5], [.96, .96, .025], '#b9bfc0')]),
    'food_box': dict(matt=[.24, .18, .07], grepp=[0, -.08, -.035], delar=[
        del_('lada', [0, 0, 0], [1, 1, 1], '#b4956b')]),
    'card_payment_terminal': dict(matt=[.09, .16, .06], grepp=[0, 0, -.03], delar=[
        del_('lada', [0, 0, 0], [1, 1, 1], '#343a40'),
        del_('lada', [0, .2, .51], [.8, .4, .025], '#698c94')]),
    'coin': dict(matt=[.024, .024, .002], grepp=[0, 0, 0], delar=[
        del_('cylinder', [0, 0, 0], [1, 1, 1], '#c9aa67')]),
    'kebab_cutter': dict(matt=[.12, .22, .12], grepp=[0, -.06, 0], delar=[
        del_('lada', [0, 0, 0], [.65, 1, .65], '#394044'),
        del_('cylinder', [0, .35, 0], [1, 1, .15], '#b7bdc0')]),
    'mini_pizza': dict(matt=[.28, .28, .035], grepp=[0, -.11, -.015], delar=[TALLRIK,
        del_('ellipsoid', [0, 0, .2], [.5, .4, .8], '#c58b41'),
        del_('ellipsoid', [.06, 0, .45], [.35, .3, .3], '#e2bb43')]),
    'hamburger': dict(matt=[.13, .13, .09], grepp=[0, 0, -.045], delar=[
        del_('lada', [0, 0, -.44], [1.6, 1.5, .06], '#b8986c'),
        del_('ellipsoid', [0, 0, -.18], [1, 1, .4], '#bf863f'),
        del_('cylinder', [0, 0, .02], [.95, .95, .22], '#654130'),
        del_('lada', [0, 0, .14], [.95, .95, .05], '#e7b637'),
        del_('ellipsoid', [0, 0, .30], [1, 1, .5], '#c9934b')]),
    'fiktiv_molnfrukt': dict(matt=[.30, .20, .13], grepp=[0, 0, -.065], fiktiv=True, delar=[PAPPER,
        del_('ellipsoid', [0, 0, .15], [.9, .8, .8], '#9b42da'),
        del_('ellipsoid', [.15, .05, .45], [.4, .3, .4], '#40d4ce')]),
}

def hamta(typ):
    if typ not in BANK:
        raise ValueError('Ingen form i propbanken: ' + typ)
    return dict(copy.deepcopy(BANK[typ]), typ=typ, status='mall', modell_ref=None,
                metod='Parametrisk form; dolda sidor och grepp är antagna bankvärden.')
