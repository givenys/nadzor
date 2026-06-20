import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { page_routes } from '../config/page_routes';
import '../styles/Header.css';


function Header() {

    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const location = useLocation();

    const toggleMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
    const closeMenu = () => setIsMobileMenuOpen(false);

    const navLinks = page_routes.filter((r) => r.label);
 
    return (
        
        <header className='App-header'>
            <div className='header-container'>

                <div className='header-logo'>
                    <Link to='/' onClick={closeMenu}>Надзор – система ИИ видеоаналитики</Link>
                </div>
                
                {/* ham burger button for mobiles */}
                <button
                    className='hamburger-btn'
                    onClick={toggleMenu}
                    aria-label='Toggle menu'
                    aria-expanded={isMobileMenuOpen}
                >
                    <span className={`hamburger-icon ${isMobileMenuOpen ? 'open' : ''}`}>
                    </span>
                </button>

                {/* pc menu */}
                <nav className='App-header-nav desktop-nav'>
                    {navLinks.map((r) => {

                        // div PC classnames
                        // const baseClasses = `nav-link ${location.pathname === r.path ? 'active' : ''}`;
                        // const overrideStyles = r.props?.override_styles?.join(' ') || '';
                        // const selectedClasses = (overrideStyles || baseClasses).trim();
                        const isActive = location.pathname === r.path;

                        const classes = [
                            'nav-link', 
                            ...(r.props?.override_styles || []), 
                            isActive && 'active'
                        ].filter(Boolean).join(' ');
                        console.log(classes, '\n');


                        return ( 
                            <Link
                                key={r.path}
                                to={r.path}
                                // className={`nav-link ${location.pathname === r.path ? 'active' : ''}`}
                                className={classes}
                                data-route={r.path}
                            >
                                {r.label}
                            </Link>
                        );
                        })}
                </nav>

            </div>

            <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
                <nav className='mobile-nav'>
                    {navLinks.map((r) => (
                        <Link
                            key={r.path}
                            to={r.path}
                            className={`mobile-nav-link ${location.pathname === r.path ? 'active' : ''}`}
                            onClick={closeMenu}
                        >
                            {r.label}
                        </Link>
                    ))}
                </nav>
            </div>
            
            {/* background shadowing */}
            {isMobileMenuOpen && (
                <div className='menu-overlay' onClick={closeMenu}></div>
            )}

        </header>

    );
}

export default Header;


// return (
//        <header className='App-header'>
//            <nav className='App-header-nav'>
//               {page_routes
//                    .filter((r) => r.label)
//                    .map((r) => (
//                        <Link key={r.path} to={r.path} className='nav-link'>
//                           {r.label}
//                        </Link>
//                    ):)}
//           </nav>
//        </header>
//    );
